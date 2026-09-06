"""
Anomaly classification from computed features.
Maps z-scores and ratios to normalized 0–100 scores.
"""
from app.services.intelligence.features import StockFeatures
import math


def score_price_anomaly(z_score: float) -> float:
    """Convert absolute z-score to 0–100 anomaly score."""
    abs_z = abs(z_score)
    if abs_z < 1.0:
        return abs_z * 20       # 0–20 for |z| < 1
    elif abs_z < 2.0:
        return 20 + (abs_z - 1) * 30   # 20–50 for |z| 1–2
    elif abs_z < 3.0:
        return 50 + (abs_z - 2) * 30   # 50–80 for |z| 2–3
    else:
        return min(100, 80 + (abs_z - 3) * 10)   # 80–100 for |z| > 3


def score_volume_anomaly(volume_ratio: float) -> float:
    """Convert volume ratio to 0–100 score."""
    if volume_ratio <= 1.0:
        return 0.0
    elif volume_ratio <= 1.5:
        return (volume_ratio - 1.0) * 40   # 0–20
    elif volume_ratio <= 2.0:
        return 20 + (volume_ratio - 1.5) * 60   # 20–50
    elif volume_ratio <= 3.0:
        return 50 + (volume_ratio - 2.0) * 30   # 50–80
    else:
        return min(100, 80 + (volume_ratio - 3.0) * 10)


def score_volatility_anomaly(features: StockFeatures) -> float:
    """Score based on whether current movement exceeds historical volatility."""
    if features.std_return <= 0:
        return 0.0
    # How many times today's move exceeds 1-sigma?
    ratio = abs(features.current_return) / features.std_return
    return min(100, ratio * 25)


def classify_severity(attention_score: float) -> str:
    """Map attention score to severity label."""
    if attention_score >= 80:
        return "MAJOR"
    elif attention_score >= 60:
        return "IMPORTANT"
    elif attention_score >= 30:
        return "WATCH"
    else:
        return "NORMAL"
