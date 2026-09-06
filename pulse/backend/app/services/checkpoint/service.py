"""
Checkpoint Service — saves and retrieves user market state.
This is the CORE of PULSE: remembering what the user last saw.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.checkpoint import Checkpoint
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.models.stock import Stock
from app.models.market_snapshot import MarketSnapshot
from app.services.market.provider import yfinance_provider
import logging

logger = logging.getLogger(__name__)


def save_checkpoint(user_id: int, watchlist_id: int, db: Session) -> int:
    """
    Save current market state as user checkpoint.
    Called whenever a user views their watchlist.
    Returns number of stocks checkpointed.
    """
    wl_stocks = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == watchlist_id
    ).all()

    count = 0
    for ws in wl_stocks:
        stock: Stock = ws.stock
        if not stock:
            continue

        try:
            # Get current price from latest snapshot
            snap = (
                db.query(MarketSnapshot)
                .filter(MarketSnapshot.stock_id == stock.id)
                .order_by(MarketSnapshot.collected_at.desc())
                .first()
            )

            if snap:
                price = snap.price
                volume = snap.volume
            else:
                raw = yfinance_provider.get_quote(stock.symbol)
                if not raw:
                    continue
                price = raw["price"]
                volume = raw.get("volume")

            cp = Checkpoint(
                user_id=user_id,
                watchlist_id=watchlist_id,
                stock_id=stock.id,
                price=price,
                volume=volume,
                attention_score=0.0,
            )
            db.add(cp)
            count += 1

        except Exception as e:
            logger.error(f"Checkpoint failed for {stock.symbol}: {e}")

    db.commit()
    return count


def get_last_checkpoint_time(user_id: int, watchlist_id: int, db: Session) -> Optional[datetime]:
    """Get when the user last checked this watchlist."""
    cp = (
        db.query(Checkpoint)
        .filter(
            Checkpoint.user_id == user_id,
            Checkpoint.watchlist_id == watchlist_id,
        )
        .order_by(Checkpoint.created_at.desc())
        .first()
    )
    return cp.created_at if cp else None
