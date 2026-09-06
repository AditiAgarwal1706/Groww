"""
Tests for intelligence pipeline: feature extraction, anomaly z-scores,
attention scoring, movement attribution, and change detection.
"""
from app.services.intelligence.features import compute_features
from app.services.intelligence.attention import compute_attention_score
from app.services.intelligence.attribution import compute_attribution
from app.services.intelligence.change_detector import run_change_detection


def test_feature_extraction_normal():
    prices = [100, 101, 99, 100, 102, 101, 100, 101, 100, 102]
    volumes = [1000] * 10
    feat = compute_features(
        symbol="AAPL",
        price_history=prices,
        volume_history=volumes,
        current_price=101.5,
        current_volume=1100,
        checkpoint_price=100.0,
    )
    assert feat.symbol == "AAPL"
    assert feat.volume_ratio == 1.1
    assert abs(feat.current_return - 0.015) < 1e-4
    assert feat.price_z_score < 2.0


def test_feature_extraction_anomaly():
    prices = [100.0] * 20
    volumes = [1000.0] * 20
    feat = compute_features(
        symbol="TSLA",
        price_history=prices,
        volume_history=volumes,
        current_price=120.0,  # 20% spike
        current_volume=5000,  # 5x volume
        checkpoint_price=100.0,
    )
    assert feat.volume_ratio == 5.0
    assert feat.price_z_score > 3.0


def test_attention_score_severity_tiers():
    prices = [100.0] * 10
    volumes = [1000.0] * 10

    # Normal activity
    feat_normal = compute_features("AAPL", prices, volumes, 100.5, 1000, 100.0)
    att_normal = compute_attention_score(feat_normal, news_impact=0.0, relative_performance=0.0)
    assert att_normal.severity in ["NORMAL", "WATCH"]

    # Major anomaly activity
    feat_major = compute_features("AAPL", prices, volumes, 125.0, 4000, 100.0)
    att_major = compute_attention_score(feat_major, news_impact=0.9, relative_performance=0.15)
    assert att_major.attention_score >= 60
    assert att_major.severity in ["IMPORTANT", "MAJOR"]


def test_movement_attribution_calculation():
    attr = compute_attribution(
        stock_return=-0.05,
        sector_etf="XLK",
        period_days=1,
    )
    assert attr.stock_return == -0.05
    assert abs((attr.company_pct + attr.sector_pct + attr.market_pct) - 100.0) < 1e-2



def test_change_detection_pipeline(db_session, test_user, test_watchlist):
    changes = run_change_detection(
        user_id=test_user.id,
        watchlist_id=test_watchlist.id,
        db=db_session,
    )
    assert isinstance(changes, list)
    assert len(changes) == 1
    ch = changes[0]
    assert ch.symbol == "NVDA"
    assert ch.attention_score >= 0
    assert ch.severity in ["NORMAL", "WATCH", "IMPORTANT", "MAJOR"]
