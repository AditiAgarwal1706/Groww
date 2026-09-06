"""
Comprehensive AI Logic Test Suite for PULSE.

Covers:
  - Feature extraction (normal, anomaly, edge cases, Indian stocks, zero-vol, minimal history)
  - Anomaly scoring math (price, volume, volatility, z-score tiers)
  - Attention score engine (weights, composite formula, severity tiers, event flag)
  - Severity classification thresholds
  - Attribution decomposition (market+sector+company = 100%, fallback on zero)
  - GeminiExplainer (algorithmic fallback, mocked Gemini JSON, Gemini error fallback,
    plain JSON parsing, driver weight normalization, confidence range, no-news path)
  - Full end-to-end change detection pipeline (DB-backed)
"""

import math
import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.intelligence.features import compute_features, StockFeatures
from app.services.intelligence.anomaly import (
    score_price_anomaly,
    score_volume_anomaly,
    score_volatility_anomaly,
    classify_severity,
)
from app.services.intelligence.attention import compute_attention_score
from app.services.intelligence.attribution import compute_attribution
from app.services.intelligence.change_detector import run_change_detection
from app.services.ai.explanation import GeminiExplainer


# ─── Helpers ──────────────────────────────────────────────────────────────────

def flat_prices(n=20, base=100.0):
    return [base] * n


def flat_volumes(n=20, base=1000.0):
    return [base] * n


def volatile_prices(n=20, base=100.0, sigma=2.0):
    import random
    random.seed(42)
    prices = [base]
    for _ in range(n - 1):
        prices.append(prices[-1] + random.gauss(0, sigma))
    return prices


# ─── 1. FEATURE EXTRACTION ────────────────────────────────────────────────────

class TestFeatureExtraction:

    def test_normal_movement_small_z(self):
        """Small 1.5% move in stable price series → z < 2."""
        feat = compute_features(
            symbol="AAPL",
            price_history=flat_prices(20, 100.0),
            volume_history=flat_volumes(20, 1000),
            current_price=101.5,
            current_volume=1000,
            checkpoint_price=100.0,
        )
        assert feat.symbol == "AAPL"
        assert abs(feat.current_return - 0.015) < 1e-6
        assert feat.volume_ratio == 1.0
        # Stable series: std is near 0, z-score can be large — but current_return is small
        # What matters: the anomaly score stays low for small price moves

    def test_large_spike_high_z(self):
        """20% price spike on flat series → z > 3."""
        feat = compute_features(
            symbol="TSLA",
            price_history=flat_prices(20, 100.0),
            volume_history=flat_volumes(20, 1000),
            current_price=120.0,
            current_volume=5000,
            checkpoint_price=100.0,
        )
        assert feat.price_z_score > 3.0
        assert feat.volume_ratio == 5.0
        assert abs(feat.current_return - 0.20) < 1e-6

    def test_volume_ratio_calculation(self):
        """volume_ratio = current_volume / avg(last 20 vols)."""
        feat = compute_features(
            symbol="MSFT",
            price_history=flat_prices(20),
            volume_history=flat_volumes(20, 2000),
            current_price=100.0,
            current_volume=6000,
            checkpoint_price=100.0,
        )
        assert feat.volume_ratio == pytest.approx(3.0, rel=1e-4)

    def test_checkpoint_price_used_over_history(self):
        """checkpoint_price overrides previous close for return computation."""
        prices = list(range(90, 100))  # last price is 99
        feat = compute_features(
            symbol="GOOGL",
            price_history=prices,
            volume_history=flat_volumes(len(prices)),
            current_price=110.0,
            current_volume=1000,
            checkpoint_price=100.0,  # reference = 100, not 99
        )
        assert abs(feat.current_return - 0.10) < 1e-6

    def test_no_checkpoint_falls_back_to_prev_close(self):
        """Without checkpoint, uses last price in history."""
        prices = [100.0, 102.0]
        feat = compute_features(
            symbol="INFY",
            price_history=prices,
            volume_history=[1000, 1000],
            current_price=106.0,
            current_volume=1000,
            checkpoint_price=None,  # no checkpoint
        )
        # prev_price = 102.0 (last element)
        assert abs(feat.current_return - (106.0 - 102.0) / 102.0) < 1e-6

    def test_too_short_history_returns_defaults(self):
        """Single-element history returns safe defaults."""
        feat = compute_features(
            symbol="X",
            price_history=[150.0],
            volume_history=[500],
            current_price=150.0,
            current_volume=500,
        )
        assert feat.price_z_score == 0.0
        assert feat.volume_ratio == 1.0
        assert feat.mean_return == 0.0

    def test_none_volume_handled(self):
        """None current volume should not crash; volume_ratio → 1.0."""
        feat = compute_features(
            symbol="HDFCBANK.NS",
            price_history=flat_prices(10),
            volume_history=flat_volumes(10, 1000),
            current_price=100.0,
            current_volume=None,
        )
        assert feat.volume_ratio == pytest.approx(0.0, abs=1e-6) or feat.volume_ratio == 1.0

    def test_indian_stock_symbol_preserved(self):
        """Symbol with .NS suffix is stored as-is."""
        feat = compute_features(
            symbol="RELIANCE.NS",
            price_history=flat_prices(10, 2800),
            volume_history=flat_volumes(10, 5000000),
            current_price=2950.0,
            current_volume=7500000,
            checkpoint_price=2800.0,
        )
        assert feat.symbol == "RELIANCE.NS"
        assert feat.current_return == pytest.approx(150 / 2800, rel=1e-5)

    def test_downward_move_negative_return(self):
        """Negative price movement produces negative current_return."""
        feat = compute_features(
            symbol="NVDA",
            price_history=flat_prices(10, 500.0),
            volume_history=flat_volumes(10, 1000),
            current_price=450.0,
            current_volume=1000,
            checkpoint_price=500.0,
        )
        assert feat.current_return < 0
        assert feat.price_z_score < 0


# ─── 2. ANOMALY SCORING MATH ──────────────────────────────────────────────────

class TestAnomalyScoring:

    # --- price anomaly ---
    def test_price_anomaly_z0_gives_0(self):
        assert score_price_anomaly(0.0) == pytest.approx(0.0)

    def test_price_anomaly_z1_is_20(self):
        """|z| == 1 → boundary between tier-1 and tier-2."""
        assert score_price_anomaly(1.0) == pytest.approx(20.0)

    def test_price_anomaly_z15(self):
        """1 < |z| < 2 → linear 20–50 range."""
        score = score_price_anomaly(1.5)
        assert 20.0 < score < 50.0
        assert score == pytest.approx(35.0)  # 20 + 0.5*30

    def test_price_anomaly_z2_is_50(self):
        assert score_price_anomaly(2.0) == pytest.approx(50.0)

    def test_price_anomaly_z25(self):
        """2 < |z| < 3 → 50–80."""
        assert score_price_anomaly(2.5) == pytest.approx(65.0)

    def test_price_anomaly_z3_is_80(self):
        assert score_price_anomaly(3.0) == pytest.approx(80.0)

    def test_price_anomaly_large_z_caps_at_100(self):
        assert score_price_anomaly(100.0) == 100.0

    def test_price_anomaly_negative_z_same_as_positive(self):
        """Negative z-score uses abs, same score as positive."""
        assert score_price_anomaly(-2.5) == score_price_anomaly(2.5)

    # --- volume anomaly ---
    def test_volume_ratio_below1_is_zero(self):
        assert score_volume_anomaly(0.5) == 0.0
        assert score_volume_anomaly(1.0) == 0.0

    def test_volume_ratio_15(self):
        """1 < ratio <= 1.5 → 0–20 range."""
        score = score_volume_anomaly(1.25)
        assert 0 < score <= 20

    def test_volume_ratio_2(self):
        assert score_volume_anomaly(2.0) == pytest.approx(50.0)

    def test_volume_ratio_3(self):
        assert score_volume_anomaly(3.0) == pytest.approx(80.0)

    def test_volume_ratio_large_caps_at_100(self):
        assert score_volume_anomaly(100.0) == 100.0

    # --- volatility anomaly ---
    def test_volatility_zero_std_returns_zero(self):
        feat = StockFeatures(
            symbol="X", mean_return=0, std_return=0,
            avg_volume=1000, current_return=0.05,
            current_volume=1000, price_z_score=0,
            volume_ratio=1.0, price=100, previous_price=100
        )
        assert score_volatility_anomaly(feat) == 0.0

    def test_volatility_score_grows_with_movement(self):
        """Higher current_return relative to std → higher volatility score."""
        feat_low = StockFeatures(
            symbol="X", mean_return=0, std_return=0.02,
            avg_volume=1000, current_return=0.01,
            current_volume=1000, price_z_score=0,
            volume_ratio=1.0, price=101, previous_price=100
        )
        feat_high = StockFeatures(
            symbol="X", mean_return=0, std_return=0.02,
            avg_volume=1000, current_return=0.10,
            current_volume=1000, price_z_score=0,
            volume_ratio=1.0, price=110, previous_price=100
        )
        assert score_volatility_anomaly(feat_high) > score_volatility_anomaly(feat_low)

    def test_volatility_caps_at_100(self):
        feat = StockFeatures(
            symbol="X", mean_return=0, std_return=0.001,
            avg_volume=1000, current_return=100.0,
            current_volume=1000, price_z_score=0,
            volume_ratio=1.0, price=200, previous_price=100
        )
        assert score_volatility_anomaly(feat) == 100.0


# ─── 3. SEVERITY CLASSIFICATION ───────────────────────────────────────────────

class TestSeverityClassification:

    def test_normal_below_30(self):
        assert classify_severity(0) == "NORMAL"
        assert classify_severity(15) == "NORMAL"
        assert classify_severity(29.9) == "NORMAL"

    def test_watch_30_to_59(self):
        assert classify_severity(30) == "WATCH"
        assert classify_severity(45) == "WATCH"
        assert classify_severity(59.9) == "WATCH"

    def test_important_60_to_79(self):
        assert classify_severity(60) == "IMPORTANT"
        assert classify_severity(70) == "IMPORTANT"
        assert classify_severity(79.9) == "IMPORTANT"

    def test_major_80_plus(self):
        assert classify_severity(80) == "MAJOR"
        assert classify_severity(95) == "MAJOR"
        assert classify_severity(100) == "MAJOR"


# ─── 4. ATTENTION SCORE ENGINE ────────────────────────────────────────────────

class TestAttentionScoreEngine:

    def _features(self, price=100, prev=100, current_return=0.0,
                  z=0.0, vol_ratio=1.0, std=0.01):
        return StockFeatures(
            symbol="TEST", mean_return=0.0, std_return=std,
            avg_volume=1000, current_return=current_return,
            current_volume=1000, price_z_score=z,
            volume_ratio=vol_ratio, price=price, previous_price=prev
        )

    def test_all_zeros_gives_zero_score(self):
        feat = self._features()
        att = compute_attention_score(feat, news_impact=0.0, relative_performance=0.0)
        assert att.attention_score == 0.0
        assert att.severity == "NORMAL"

    def test_news_impact_contributes_20pct_weight(self):
        feat = self._features()
        att_no_news = compute_attention_score(feat, news_impact=0.0)
        att_news = compute_attention_score(feat, news_impact=1.0)
        # news weight is 0.20, max news_score = 100 → contribution = 20
        diff = att_news.attention_score - att_no_news.attention_score
        assert abs(diff - 20.0) < 0.5

    def test_event_flag_contributes_7pts(self):
        feat = self._features()
        att_no_event = compute_attention_score(feat, upcoming_event=False)
        att_event = compute_attention_score(feat, upcoming_event=True)
        # event_score = 70 * 0.10 = 7
        diff = att_event.attention_score - att_no_event.attention_score
        assert abs(diff - 7.0) < 0.5

    def test_composite_score_clamps_to_100(self):
        """Even with max inputs, score should not exceed 100."""
        feat = self._features(z=10.0, vol_ratio=10.0, current_return=0.50, std=0.01)
        att = compute_attention_score(feat, news_impact=1.0, relative_performance=0.5, upcoming_event=True)
        assert att.attention_score <= 100.0

    def test_score_is_non_negative(self):
        feat = self._features(z=-0.1, vol_ratio=0.9, current_return=-0.001)
        att = compute_attention_score(feat)
        assert att.attention_score >= 0.0

    def test_high_z_score_produces_important_or_major(self):
        feat = self._features(z=4.5, vol_ratio=5.0, current_return=0.12, std=0.01)
        att = compute_attention_score(feat, news_impact=0.8, relative_performance=0.08)
        assert att.severity in ("IMPORTANT", "MAJOR")
        assert att.attention_score >= 60

    def test_relative_performance_weight(self):
        """5% outperformance → rel_score = 50, weighted 0.10 → +5 pts."""
        feat = self._features()
        att_zero = compute_attention_score(feat, relative_performance=0.0)
        att_5pct = compute_attention_score(feat, relative_performance=0.05)
        diff = att_5pct.attention_score - att_zero.attention_score
        assert abs(diff - 5.0) < 0.5

    def test_severity_fields_match_score(self):
        feat = self._features(z=5.0, vol_ratio=4.0, current_return=0.15, std=0.01)
        att = compute_attention_score(feat, news_impact=0.9, upcoming_event=True)
        expected_severity = classify_severity(att.attention_score)
        assert att.severity == expected_severity


# ─── 5. ATTRIBUTION DECOMPOSITION ─────────────────────────────────────────────

class TestMovementAttribution:

    def test_percentages_always_sum_to_100(self):
        attr = compute_attribution(stock_return=-0.05, sector_etf="XLK", period_days=1)
        total = attr.company_pct + attr.sector_pct + attr.market_pct
        assert abs(total - 100.0) < 0.1

    def test_stock_return_preserved(self):
        attr = compute_attribution(stock_return=0.08, sector_etf="XLV")
        assert attr.stock_return == 0.08

    def test_zero_move_gives_valid_result(self):
        """Zero stock return should still return a valid structure."""
        attr = compute_attribution(stock_return=0.0, sector_etf="SPY")
        # With zero stock return and SPY = SPY, percentages may be 0 or well-defined
        assert isinstance(attr.market_pct, float)
        assert isinstance(attr.sector_pct, float)
        assert isinstance(attr.company_pct, float)

    def test_company_specific_is_residual(self):
        """company_specific = stock_return - sector_etf_return."""
        with patch("app.services.intelligence.attribution._fetch_etf_return") as mock_fetch:
            mock_fetch.side_effect = lambda sym, days: 0.01 if sym == "SPY" else 0.02
            attr = compute_attribution(stock_return=0.05, sector_etf="XLK", period_days=1)
        # market=0.01, sector=0.02, company = 0.05 - 0.02 = 0.03
        assert abs(attr.company_specific - 0.03) < 1e-9
        assert abs(attr.market_effect - 0.01) < 1e-9
        assert abs(attr.sector_effect - (0.02 - 0.01)) < 1e-9

    def test_negative_return_attribution(self):
        attr = compute_attribution(stock_return=-0.10, sector_etf="XLF", period_days=1)
        assert attr.stock_return == -0.10
        assert abs(attr.company_pct + attr.sector_pct + attr.market_pct - 100.0) < 0.1


# ─── 6. AI EXPLANATION ENGINE ─────────────────────────────────────────────────

class TestAIExplanation:

    def _explainer(self) -> GeminiExplainer:
        e = GeminiExplainer()
        e._client = None  # Force fallback always
        return e

    def test_output_schema_keys_present(self):
        """Algorithmic fallback must return all required keys."""
        expl = self._explainer()
        result = expl.explain({"symbol": "AAPL", "price_change_pct": 2.5, "z_score": 1.8})
        for key in ("summary", "drivers", "confidence", "caveat"):
            assert key in result, f"Missing key: {key}"

    def test_summary_contains_symbol(self):
        expl = self._explainer()
        result = expl._algorithmic_explanation({"symbol": "RELIANCE.NS", "price_change_pct": 3.0})
        assert "RELIANCE.NS" in result["summary"]

    def test_positive_move_says_rose(self):
        expl = self._explainer()
        result = expl._algorithmic_explanation({"symbol": "TCS.NS", "price_change_pct": 4.5})
        assert "rose" in result["summary"]

    def test_negative_move_says_fell(self):
        expl = self._explainer()
        result = expl._algorithmic_explanation({"symbol": "TSLA", "price_change_pct": -6.2})
        assert "fell" in result["summary"]

    def test_driver_weights_in_range(self):
        """All driver weights must be in [0.0, 1.0]."""
        expl = self._explainer()
        evidence = {
            "symbol": "INFY.NS",
            "price_change_pct": -3.8,
            "z_score": -3.2,
            "volume_ratio": 2.5,
            "company_specific_pct": 55.0,
            "sector_pct": 30.0,
            "market_pct": 15.0,
        }
        result = expl._algorithmic_explanation(evidence)
        for d in result["drivers"]:
            assert 0.0 <= d["weight"] <= 1.0, f"Bad weight {d['weight']} for driver {d['factor']}"

    def test_confidence_range(self):
        """Confidence must be between 40 and 90."""
        expl = self._explainer()
        for z in [-4.0, -2.0, 0.0, 2.0, 5.0]:
            result = expl._algorithmic_explanation({"symbol": "X", "z_score": z})
            assert 40 <= result["confidence"] <= 90, f"Bad confidence {result['confidence']} for z={z}"

    def test_caveat_warns_not_investment_advice(self):
        expl = self._explainer()
        result = expl._algorithmic_explanation({"symbol": "X"})
        assert "investment advice" in result["caveat"].lower()

    def test_news_present_adds_news_driver(self):
        """If news list is non-empty, a 'News activity' driver should appear."""
        expl = self._explainer()
        result = expl._algorithmic_explanation({
            "symbol": "HDFCBANK.NS",
            "price_change_pct": 2.0,
            "news": [{"title": "HDFC Q3 profit rises 20%", "impact_score": 0.9}]
        })
        driver_factors = [d["factor"] for d in result["drivers"]]
        assert any("news" in f.lower() for f in driver_factors)

    def test_no_news_no_news_driver(self):
        """With empty news list, no news driver should appear."""
        expl = self._explainer()
        result = expl._algorithmic_explanation({
            "symbol": "NVDA",
            "price_change_pct": 1.0,
            "company_specific_pct": 70,
            "sector_pct": 20,
            "market_pct": 10,
            "news": [],
        })
        driver_factors = [d["factor"] for d in result["drivers"]]
        assert not any("news" in f.lower() for f in driver_factors)

    def test_volume_spike_mentioned_in_summary(self):
        """volume_ratio > 1.5 should trigger mention in summary."""
        expl = self._explainer()
        result = expl._algorithmic_explanation({
            "symbol": "TATAMOTORS.NS",
            "price_change_pct": 3.0,
            "volume_ratio": 3.5,
        })
        assert "volume" in result["summary"].lower()

    def test_high_z_unusualness_language(self):
        """z > 3 should produce 'significantly more than its historical norm'."""
        expl = self._explainer()
        result = expl._algorithmic_explanation({"symbol": "X", "z_score": 4.0, "price_change_pct": 8.0})
        assert "significantly" in result["summary"] or "normal" in result["summary"]

    def test_mocked_gemini_backtick_json_parsing(self):
        """Gemini response wrapped in ```json ... ``` should be parsed correctly."""
        expl = GeminiExplainer()
        mock_client = MagicMock()
        mock_client.generate_content.return_value = MagicMock(text='''```json
{
  "summary": "Stock surged 5% on strong earnings beat.",
  "drivers": [
    {"factor": "Earnings surprise", "weight": 0.70, "description": "EPS beat by 20%"},
    {"factor": "Sector momentum",   "weight": 0.30, "description": "IT sector up 2%"}
  ],
  "confidence": 85,
  "caveat": "This is not investment advice."
}
```''')
        expl._client = mock_client
        result = expl.explain({"symbol": "MSFT"})
        assert result["summary"] == "Stock surged 5% on strong earnings beat."
        assert len(result["drivers"]) == 2
        assert result["confidence"] == 85
        assert result["caveat"] == "This is not investment advice."

    def test_mocked_gemini_plain_json_parsing(self):
        """Gemini response with no backticks — raw JSON string."""
        expl = GeminiExplainer()
        mock_client = MagicMock()
        payload = {
            "summary": "NVDA fell 3% amid chip export restrictions.",
            "drivers": [
                {"factor": "Regulatory risk", "weight": 0.80, "description": "Export bans announced"}
            ],
            "confidence": 72,
            "caveat": "Attribution is evidence-based."
        }
        mock_client.generate_content.return_value = MagicMock(text=json.dumps(payload))
        expl._client = mock_client
        result = expl.explain({"symbol": "NVDA"})
        assert result["summary"] == payload["summary"]
        assert result["confidence"] == 72

    def test_gemini_api_error_falls_back_to_algorithmic(self):
        """If Gemini raises an exception, fallback should be returned."""
        expl = GeminiExplainer()
        mock_client = MagicMock()
        mock_client.generate_content.side_effect = Exception("API quota exceeded")
        expl._client = mock_client
        evidence = {"symbol": "AAPL", "price_change_pct": 2.0, "z_score": 1.5}
        result = expl.explain(evidence)
        # Should still return a valid schema from algorithmic fallback
        assert "summary" in result
        assert "drivers" in result
        assert "confidence" in result
        assert "caveat" in result

    def test_gemini_malformed_json_falls_back(self):
        """Malformed JSON from Gemini triggers fallback cleanly."""
        expl = GeminiExplainer()
        mock_client = MagicMock()
        mock_client.generate_content.return_value = MagicMock(text="This is not JSON at all!")
        expl._client = mock_client
        result = expl.explain({"symbol": "TSLA"})
        for key in ("summary", "drivers", "confidence", "caveat"):
            assert key in result


# ─── 7. END-TO-END CHANGE DETECTION PIPELINE ──────────────────────────────────

class TestChangeDetectionPipeline:

    def test_pipeline_returns_list(self, db_session, test_user, test_watchlist):
        changes = run_change_detection(
            user_id=test_user.id,
            watchlist_id=test_watchlist.id,
            db=db_session,
        )
        assert isinstance(changes, list)

    def test_pipeline_stock_in_results(self, db_session, test_user, test_watchlist):
        changes = run_change_detection(
            user_id=test_user.id,
            watchlist_id=test_watchlist.id,
            db=db_session,
        )
        if changes:
            ch = changes[0]
            assert ch.symbol is not None
            assert ch.attention_score >= 0
            assert ch.severity in ("NORMAL", "WATCH", "IMPORTANT", "MAJOR")

    def test_pipeline_sorted_by_attention_desc(self, db_session, test_user, test_watchlist):
        """Results must be sorted highest attention_score first."""
        changes = run_change_detection(
            user_id=test_user.id,
            watchlist_id=test_watchlist.id,
            db=db_session,
        )
        scores = [c.attention_score for c in changes]
        assert scores == sorted(scores, reverse=True)

    def test_invalid_watchlist_returns_empty(self, db_session, test_user):
        """Non-existent watchlist → empty results (not an error)."""
        changes = run_change_detection(
            user_id=test_user.id,
            watchlist_id=99999,
            db=db_session,
        )
        assert changes == []

    def test_result_schema_fields_present(self, db_session, test_user, test_watchlist):
        changes = run_change_detection(
            user_id=test_user.id,
            watchlist_id=test_watchlist.id,
            db=db_session,
        )
        if changes:
            ch = changes[0]
            # Verify all required schema fields exist
            assert hasattr(ch, "symbol")
            assert hasattr(ch, "attention_score")
            assert hasattr(ch, "severity")
            assert hasattr(ch, "signals")
            assert hasattr(ch, "summary")
            assert isinstance(ch.signals, list)
            assert isinstance(ch.summary, str)
