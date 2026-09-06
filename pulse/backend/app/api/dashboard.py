from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.models.stock import Stock
from app.models.market_snapshot import MarketSnapshot
from app.schemas.change import DashboardResponse, DashboardStock, ChangeSummary, DetectedChangeResponse
from app.services.checkpoint.service import get_last_checkpoint_time
from app.services.intelligence.change_detector import run_change_detection
from app.services.intelligence.features import compute_features
from app.services.intelligence.attention import compute_attention_score
from app.services.market.service import market_service
from datetime import datetime, timezone, timedelta
import logging

router = APIRouter(prefix="/api", tags=["dashboard"])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    sync_live: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Single aggregated dashboard endpoint.
    Returns: last check time, change summary, top attention items, full watchlist.
    """
    # Get user's first watchlist (or create one)
    watchlist = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).order_by(Watchlist.created_at.asc()).first()

    if not watchlist:
        return DashboardResponse(
            last_checked_at=None,
            summary=ChangeSummary(major=0, important=0, watch=0, normal=0, total=0),
            top_attention=[],
            watchlist=[],
            watchlist_id=None,
            watchlist_name=None,
        )

    # Fetch watchlist stocks
    wl_stocks = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == watchlist.id
    ).all()
    tracked_stocks = [ws.stock for ws in wl_stocks if ws.stock]

    # Sync live quotes from yfinance if requested or if snapshots are stale
    if tracked_stocks:
        latest_snap = (
            db.query(MarketSnapshot)
            .filter(MarketSnapshot.stock_id.in_([s.id for s in tracked_stocks]))
            .order_by(MarketSnapshot.collected_at.desc())
            .first()
        )
        is_stale = not latest_snap or (datetime.now(timezone.utc) - latest_snap.collected_at) > timedelta(minutes=15)
        if sync_live or is_stale:
            try:
                market_service.sync_live_quotes_for_stocks(tracked_stocks, db)
            except Exception as e:
                logger.error(f"Live market quote sync error: {e}")

    # Last checkpoint time
    last_checked = get_last_checkpoint_time(current_user.id, watchlist.id, db)

    # Run change detection
    changes = run_change_detection(current_user.id, watchlist.id, db)

    # Build summary
    summary = ChangeSummary(
        major=sum(1 for c in changes if c.severity == "MAJOR"),
        important=sum(1 for c in changes if c.severity == "IMPORTANT"),
        watch=sum(1 for c in changes if c.severity == "WATCH"),
        normal=sum(1 for c in changes if c.severity == "NORMAL"),
        total=len(changes),
    )

    # Top attention items (non-normal, sorted by score)
    top_attention = [c for c in changes if c.severity != "NORMAL"][:5]

    dashboard_stocks = []
    for ws in wl_stocks:
        stock: Stock = ws.stock
        if not stock:
            continue

        # Find matching change result
        change = next((c for c in changes if c.symbol == stock.symbol), None)

        # Get latest snapshot
        snap = (
            db.query(MarketSnapshot)
            .filter(MarketSnapshot.stock_id == stock.id)
            .order_by(MarketSnapshot.collected_at.desc())
            .first()
        )

        price = snap.price if snap else 0.0
        change_pct = snap.change_pct if snap else None
        data_status = snap.data_status if snap else "LIVE"

        dashboard_stocks.append(DashboardStock(
            symbol=stock.symbol,
            company_name=stock.company_name,
            price=price,
            change_pct=change_pct,
            attention_score=change.attention_score if change else 0.0,
            severity=change.severity if change else "NORMAL",
            volume_ratio=change.volume_ratio if change else None,
            data_status=data_status,
        ))

    # Sort by attention score
    dashboard_stocks.sort(key=lambda s: s.attention_score, reverse=True)

    return DashboardResponse(
        last_checked_at=last_checked,
        summary=summary,
        top_attention=top_attention,
        watchlist=dashboard_stocks,
        watchlist_id=watchlist.id,
        watchlist_name=watchlist.name,
    )
