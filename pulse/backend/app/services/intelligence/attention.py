"""
Attention Score Engine.
Combines price, volume, volatility, news, sector/market signals
into a single 0–100 prioritization score.
"""
from app.services.intelligence.features import StockFeatures
from app.services.intelligence.anomaly import (
    score_price_anomaly, score_volume_anomaly,
    score_volatility_anomaly, classify_severity
)
from dataclasses import dataclass
from typing import Optional


@dataclass
class AttentionResult:
    attention_score: float        # 0–100
    severity: str                 # NORMAL, WATCH, IMPORTANT, MAJOR
    price_anomaly_score: float
    volume_anomaly_score: float
    volatility_score: float
    news_impact_score: float
    relative_performance_score: float
    event_score: float


def compute_attention_score(
    features: StockFeatures,
    news_impact: float = 0.0,           # 0.0–1.0 (from news classifier)
    relative_performance: float = 0.0,  # stock_return - market_return (decimal)
    upcoming_event: bool = False,        # earnings/dividend in next 7 days
) -> AttentionResult:
    """
    Weighted attention scoring model:
        price_anomaly      × 0.30
        volume_anomaly     × 0.15
        volatility         × 0.15
        news_impact        × 0.20
        relative_perf      × 0.10
        event_score        × 0.10
    """
    price_score = score_price_anomaly(features.price_z_score)
    volume_score = score_volume_anomaly(features.volume_ratio)
    vol_score = score_volatility_anomaly(features)

    # News impact: 0.0–1.0 → 0–100
    news_score = min(100.0, news_impact * 100)

    # Relative performance: bigger outperformance/underperformance = higher score
    # relative_performance in decimal (e.g. -0.04 means stock underperformed market by 4%)
    rel_score = min(100.0, abs(relative_performance) * 1000)  # 5% diff → 50 score

    # Upcoming event score
    event_score = 70.0 if upcoming_event else 0.0

    # Weighted composite
    composite = (
        price_score * 0.30 +
        volume_score * 0.15 +
        vol_score * 0.15 +
        news_score * 0.20 +
        rel_score * 0.10 +
        event_score * 0.10
    )

    composite = round(min(100.0, max(0.0, composite)), 1)

    return AttentionResult(
        attention_score=composite,
        severity=classify_severity(composite),
        price_anomaly_score=price_score,
        volume_anomaly_score=volume_score,
        volatility_score=vol_score,
        news_impact_score=news_score,
        relative_performance_score=rel_score,
        event_score=event_score,
    )
