from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.news import News
from app.models.stock import Stock
from app.schemas.change import (
    DetectedChangeResponse, AnalysisResponse,
    AttributionResponse, ChangeSignal,
    TimelineEvent, AIExplanation
)
from app.services.intelligence.change_detector import run_change_detection
from app.services.checkpoint.service import save_checkpoint, get_last_checkpoint_time
from app.services.intelligence.features import compute_features
from app.services.intelligence.attention import compute_attention_score
from app.services.intelligence.attribution import compute_attribution
from app.services.ai.explanation import gemini_explainer
from app.services.market.provider import yfinance_provider
from app.models.market_snapshot import MarketSnapshot
from datetime import datetime, timezone, timedelta
import json
import logging

router = APIRouter(prefix="/api", tags=["changes"])
logger = logging.getLogger(__name__)


def _get_watchlist_or_404(watchlist_id: int, user_id: int, db: Session) -> Watchlist:
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return wl


@router.get("/watchlists/{watchlist_id}/changes", response_model=List[DetectedChangeResponse])
def get_changes(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get meaningful changes since user's last checkpoint."""
    _get_watchlist_or_404(watchlist_id, current_user.id, db)
    return run_change_detection(current_user.id, watchlist_id, db)


@router.post("/watchlists/{watchlist_id}/checkpoint", status_code=200)
def create_checkpoint(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save current market state as user checkpoint."""
    _get_watchlist_or_404(watchlist_id, current_user.id, db)
    count = save_checkpoint(current_user.id, watchlist_id, db)
    return {"message": f"Checkpoint saved for {count} stocks", "saved_at": datetime.now(timezone.utc)}


@router.get("/watchlists/{watchlist_id}/checkpoint")
def get_checkpoint_info(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get when user last checkpointed this watchlist."""
    _get_watchlist_or_404(watchlist_id, current_user.id, db)
    last_at = get_last_checkpoint_time(current_user.id, watchlist_id, db)
    return {"last_checked_at": last_at}


@router.get("/stocks/{symbol}/analysis", response_model=AnalysisResponse)
def get_stock_analysis(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full analysis for a single stock."""
    symbol = symbol.upper()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get current price
    snap = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock.id)
        .order_by(MarketSnapshot.collected_at.desc())
        .first()
    )
    if snap:
        current_price = snap.price
        current_volume = snap.volume
    else:
        raw = yfinance_provider.get_quote(symbol)
        if not raw:
            raise HTTPException(status_code=503, detail="Market data unavailable")
        current_price = raw["price"]
        current_volume = raw.get("volume")

    # Historical data
    raw_hist = yfinance_provider.get_history(symbol, 30)
    price_hist = [h["close"] for h in raw_hist]
    vol_hist = [h["volume"] for h in raw_hist]

    features = compute_features(
        symbol=symbol,
        price_history=price_hist,
        volume_history=vol_hist,
        current_price=current_price,
        current_volume=current_volume,
    )

    attention = compute_attention_score(features=features)
    attribution = compute_attribution(
        stock_return=features.current_return,
        sector_etf=stock.sector_etf or "SPY",
        period_days=1,
    )

    signals = []
    if abs(features.current_return) > 0.001:
        signals.append(ChangeSignal(
            type="PRICE",
            value=round(features.current_return * 100, 2),
            label=f"{features.current_return * 100:+.2f}% vs previous close",
        ))
    if features.volume_ratio > 1.3:
        signals.append(ChangeSignal(
            type="VOLUME",
            value=round(features.volume_ratio, 2),
            label=f"{features.volume_ratio:.1f}× average volume",
        ))

    return AnalysisResponse(
        symbol=symbol,
        company_name=stock.company_name,
        attention_score=attention.attention_score,
        severity=attention.severity,
        price_z_score=round(features.price_z_score, 2),
        volume_ratio=round(features.volume_ratio, 2),
        attribution=AttributionResponse(
            company_specific=attribution.company_specific,
            sector_effect=attribution.sector_effect,
            market_effect=attribution.market_effect,
            company_specific_pct=attribution.company_pct,
            sector_effect_pct=attribution.sector_pct,
            market_pct=attribution.market_pct,
        ),
        signals=signals,
        confidence=max(40, min(90, int(50 + abs(features.price_z_score) * 10))),
    )


@router.get("/stocks/{symbol}/explanation", response_model=AIExplanation)
def get_explanation(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-generated explanation for stock movement."""
    symbol = symbol.upper()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    snap = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock.id)
        .order_by(MarketSnapshot.collected_at.desc())
        .first()
    )

    current_price = snap.price if snap else 0.0
    current_volume = snap.volume if snap else 0.0

    raw_hist = yfinance_provider.get_history(symbol, 30)
    price_hist = [h["close"] for h in raw_hist]
    vol_hist = [h["volume"] for h in raw_hist]

    features = compute_features(
        symbol=symbol, price_history=price_hist, volume_history=vol_hist,
        current_price=current_price, current_volume=current_volume,
    )

    attribution = compute_attribution(
        stock_return=features.current_return,
        sector_etf=stock.sector_etf or "SPY",
    )

    # Recent news
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    news_items = (
        db.query(News)
        .filter(News.stock_id == stock.id, News.published_at >= cutoff)
        .order_by(News.impact_score.desc())
        .limit(5)
        .all()
    )

    evidence = {
        "symbol": symbol,
        "company_name": stock.company_name,
        "price_change_pct": round(features.current_return * 100, 2),
        "z_score": round(features.price_z_score, 2),
        "volume_ratio": round(features.volume_ratio, 2),
        "market_return_pct": round(attribution.market_return * 100, 2),
        "sector_return_pct": round(attribution.sector_return * 100, 2),
        "company_specific_pct": attribution.company_pct,
        "sector_pct": attribution.sector_pct,
        "market_pct": attribution.market_pct,
        "news": [{"title": n.title, "event_type": n.event_type, "impact": n.impact_score} for n in news_items],
    }

    result = gemini_explainer.explain(evidence)
    return AIExplanation(**result)


@router.get("/stocks/{symbol}/timeline", response_model=list[TimelineEvent])
def get_timeline(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Market Time Machine — events from the last 24 hours."""
    symbol = symbol.upper()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    events: list[TimelineEvent] = []

    # News events
    news_items = (
        db.query(News)
        .filter(News.stock_id == stock.id, News.published_at >= cutoff)
        .order_by(News.published_at.asc())
        .limit(10)
        .all()
    )
    for n in news_items:
        events.append(TimelineEvent(
            timestamp=n.published_at,
            event_type="NEWS",
            description=n.title[:100],
            severity="IMPORTANT" if n.impact_score > 0.7 else "WATCH",
        ))

    # Price snapshots — detect significant moves
    snaps = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock.id, MarketSnapshot.timestamp >= cutoff)
        .order_by(MarketSnapshot.timestamp.asc())
        .all()
    )
    prev_price = None
    for snap in snaps:
        if prev_price and snap.price:
            move = abs((snap.price - prev_price) / prev_price)
            if move > 0.01:  # > 1% move
                events.append(TimelineEvent(
                    timestamp=snap.timestamp,
                    event_type="PRICE_MOVE",
                    description=f"Price moved {(snap.price - prev_price) / prev_price * 100:+.1f}% to ${snap.price:.2f}",
                    severity="MAJOR" if move > 0.03 else "IMPORTANT",
                ))
        if snap.volume and snap.price:
            prev_price = snap.price

    events.sort(key=lambda e: e.timestamp)
    return events
