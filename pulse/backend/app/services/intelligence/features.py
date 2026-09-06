"""
Feature extraction from historical market data.
Computes rolling statistics for anomaly detection.
"""
import numpy as np
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class StockFeatures:
    symbol: str
    mean_return: float       # 30-day mean daily return
    std_return: float        # 30-day std of daily returns (historical volatility)
    avg_volume: float        # 20-day average volume
    current_return: float    # Today's return
    current_volume: float    # Today's volume
    price_z_score: float     # How unusual is today's return?
    volume_ratio: float      # current_volume / avg_volume
    price: float
    previous_price: float


def compute_features(
    symbol: str,
    price_history: List[float],   # List of closing prices (oldest first)
    volume_history: List[float],  # List of volumes (oldest first)
    current_price: float,
    current_volume: Optional[float] = None,
    checkpoint_price: Optional[float] = None,
) -> StockFeatures:
    """
    Compute statistical features for change detection.
    
    Uses checkpoint_price if available (user's last-seen price),
    otherwise uses previous_close from history.
    """
    if len(price_history) < 2:
        return StockFeatures(
            symbol=symbol,
            mean_return=0.0, std_return=0.01,
            avg_volume=current_volume or 1.0,
            current_return=0.0, current_volume=current_volume or 0.0,
            price_z_score=0.0, volume_ratio=1.0,
            price=current_price, previous_price=current_price,
        )

    # Compute daily returns from historical prices
    prices = np.array(price_history, dtype=float)
    returns = np.diff(prices) / prices[:-1]  # percentage returns

    mean_ret = float(np.mean(returns))
    std_ret = float(np.std(returns)) if np.std(returns) > 0 else 0.001

    # 20-day average volume
    volumes = np.array(volume_history[-20:], dtype=float) if volume_history else np.array([1.0])
    avg_vol = float(np.mean(volumes)) if len(volumes) > 0 else 1.0

    # Current return — vs checkpoint if available, else vs previous close
    prev_price = checkpoint_price if checkpoint_price else price_history[-1]
    current_ret = (current_price - prev_price) / prev_price if prev_price != 0 else 0.0

    # Z-score: how many std-devs from historical mean?
    z_score = (current_ret - mean_ret) / std_ret

    # Volume ratio
    vol_ratio = (current_volume / avg_vol) if (current_volume and avg_vol > 0) else 1.0

    return StockFeatures(
        symbol=symbol,
        mean_return=mean_ret,
        std_return=std_ret,
        avg_volume=avg_vol,
        current_return=current_ret,
        current_volume=current_volume or 0.0,
        price_z_score=z_score,
        volume_ratio=vol_ratio,
        price=current_price,
        previous_price=prev_price,
    )
