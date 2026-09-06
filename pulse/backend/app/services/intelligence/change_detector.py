"""
Change Detector — core intelligence pipeline.
Compares current market state against user checkpoint.
Produces DetectedChange records with attention scores.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.checkpoint import Checkpoint
from app.models.detected_change import DetectedChange
from app.models.news import News
from app.models.market_snapshot import MarketSnapshot
from app.services.market.provider import yfinance_provider
from app.services.intelligence.features import compute_features
from app.services.intelligence.attention import compute_attention_score
from app.services.intelligence.attribution import compute_attribution
from app.schemas.change import DetectedChangeResponse, ChangeSignal, AttributionResponse

logger = logging.getLogger(__name__)


def _get_history_from_snapshots(stock_id: int, db: Session, days: int = 30):
    """Pull historical prices from DB snapshots."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    snaps = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock_id, MarketSnapshot.timestamp >= cutoff)
        .order_by(MarketSnapshot.timestamp.asc())
        .all()
    )
    prices = [s.price for s in snaps if s.price]
    volumes = [s.volume for s in snaps if s.volume]
    return prices, volumes


def _get_news_impact(stock_id: int, since: datetime, db: Session) -> float:
    """Get max news impact score since checkpoint."""
    articles = (
        db.query(News)
        .filter(News.stock_id == stock_id, News.published_at >= since)
        .order_by(News.impact_score.desc())
        .limit(5)
        .all()
    )
    if not articles:
        return 0.0
    # Weighted: highest impact + contributions from others
    impacts = [a.impact_score for a in articles]
    return min(1.0, impacts[0] * 0.7 + sum(impacts[1:]) * 0.1)


def run_change_detection(
    user_id: int,
    watchlist_id: int,
    db: Session,
) -> List[DetectedChangeResponse]:
    """
    Full pipeline:
    1. Load latest checkpoints for user's watchlist
    2. Fetch current quotes
    3. Compute features and attention scores
    4. Store DetectedChange records
    5. Return sorted results
    """
    from app.models.watchlist import Watchlist
    from app.models.watchlist_stock import WatchlistStock

    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        return []

    wl_stocks = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == watchlist_id
    ).all()

    results = []

    for ws in wl_stocks:
        stock: Stock = ws.stock
        if not stock:
            continue

        try:
            # Get last checkpoint
            checkpoint = (
                db.query(Checkpoint)
                .filter(
                    Checkpoint.user_id == user_id,
                    Checkpoint.watchlist_id == watchlist_id,
                    Checkpoint.stock_id == stock.id,
                )
                .order_by(Checkpoint.created_at.desc())
                .first()
            )

            checkpoint_price = checkpoint.price if checkpoint else None
            checkpoint_time = checkpoint.created_at if checkpoint else (
                datetime.now(timezone.utc) - timedelta(hours=24)
            )

            # Get current price from DB or live
            latest_snap = (
                db.query(MarketSnapshot)
                .filter(MarketSnapshot.stock_id == stock.id)
                .order_by(MarketSnapshot.collected_at.desc())
                .first()
            )

            if latest_snap:
                current_price = latest_snap.price
                current_volume = latest_snap.volume
                change_pct = latest_snap.change_pct
            else:
                raw = yfinance_provider.get_quote(stock.symbol)
                if not raw:
                    continue
                current_price = raw["price"]
                current_volume = raw.get("volume")
                change_pct = raw.get("change_pct")

            # Historical data
            price_hist, vol_hist = _get_history_from_snapshots(stock.id, db, 30)
            if len(price_hist) < 5:
                # Fall back to live history
                raw_hist = yfinance_provider.get_history(stock.symbol, 30)
                price_hist = [h["close"] for h in raw_hist]
                vol_hist = [h["volume"] for h in raw_hist]

            # Compute features
            features = compute_features(
                symbol=stock.symbol,
                price_history=price_hist,
                volume_history=vol_hist,
                current_price=current_price,
                current_volume=current_volume,
                checkpoint_price=checkpoint_price,
            )

            # News impact since checkpoint
            news_impact = _get_news_impact(stock.id, checkpoint_time, db)

            # Relative performance vs market
            market_ret = 0.0
            try:
                from app.services.intelligence.attribution import _fetch_etf_return
                market_ret = _fetch_etf_return("SPY", 1)
            except Exception:
                pass

            relative_perf = features.current_return - market_ret

            # Attention score
            attention = compute_attention_score(
                features=features,
                news_impact=news_impact,
                relative_performance=relative_perf,
            )

            # Build signals list
            signals = []
            if abs(features.current_return) > 0.001:
                signals.append(ChangeSignal(
                    type="PRICE",
                    value=round(features.current_return * 100, 2),
                    label=f"{'↓' if features.current_return < 0 else '↑'} {abs(features.current_return*100):.1f}% vs checkpoint",
                ))
            if features.volume_ratio > 1.3:
                signals.append(ChangeSignal(
                    type="VOLUME",
                    value=round(features.volume_ratio, 2),
                    label=f"{features.volume_ratio:.1f}× average volume",
                ))
            if abs(relative_perf) > 0.01:
                signals.append(ChangeSignal(
                    type="SECTOR",
                    value=round(relative_perf * 100, 2),
                    label=f"{'Underperformed' if relative_perf < 0 else 'Outperformed'} market by {abs(relative_perf*100):.1f}%",
                ))
            if news_impact > 0.3:
                signals.append(ChangeSignal(
                    type="NEWS",
                    value=round(news_impact * 100, 0),
                    label=f"News activity (impact {news_impact:.0%})",
                ))

            # Build summary
            if attention.severity == "NORMAL":
                summary = f"{stock.symbol} is trading normally."
            elif attention.severity == "WATCH":
                summary = f"{stock.symbol} shows slight activity worth monitoring."
            elif attention.severity == "IMPORTANT":
                summary = f"{stock.symbol} has notable movement — {signals[0].label if signals else 'check details'}."
            else:
                summary = f"{stock.symbol} is showing major unusual activity — attention required."

            # Store in DB
            evidence = json.dumps({
                "price_z_score": features.price_z_score,
                "volume_ratio": features.volume_ratio,
                "current_return": features.current_return,
                "news_impact": news_impact,
                "market_return": market_ret,
            })

            # Upsert detected change (overwrite if exists today)
            existing = (
                db.query(DetectedChange)
                .filter(
                    DetectedChange.user_id == user_id,
                    DetectedChange.watchlist_id == watchlist_id,
                    DetectedChange.stock_id == stock.id,
                    DetectedChange.detected_at >= datetime.now(timezone.utc) - timedelta(hours=1),
                )
                .first()
            )

            if existing:
                existing.score = attention.attention_score
                existing.severity = attention.severity
                existing.summary = summary
                existing.evidence = evidence
                existing.detected_at = datetime.now(timezone.utc)
            else:
                dc = DetectedChange(
                    user_id=user_id,
                    watchlist_id=watchlist_id,
                    stock_id=stock.id,
                    change_type="COMPOSITE",
                    severity=attention.severity,
                    score=attention.attention_score,
                    summary=summary,
                    evidence=evidence,
                )
                db.add(dc)

            db.commit()

            results.append(DetectedChangeResponse(
                id=existing.id if existing else 0,
                symbol=stock.symbol,
                company_name=stock.company_name,
                severity=attention.severity,
                attention_score=attention.attention_score,
                price=current_price,
                change_pct=change_pct,
                volume_ratio=features.volume_ratio,
                signals=signals,
                summary=summary,
                detected_at=datetime.now(timezone.utc),
            ))

        except Exception as e:
            logger.error(f"Change detection failed for {stock.symbol}: {e}", exc_info=True)
            continue

    # Sort by attention score descending
    results.sort(key=lambda x: x.attention_score, reverse=True)
    return results
