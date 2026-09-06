"""
Market service — wraps yfinance provider with Redis caching and DB storage.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.services.market.provider import yfinance_provider
from app.models.stock import Stock
from app.models.market_snapshot import MarketSnapshot
from app.schemas.stock import QuoteResponse, HistoryPoint

logger = logging.getLogger(__name__)

# Try to import Redis; degrade gracefully if not available
try:
    import redis as redis_lib
    from app.core.config import settings
    _redis_client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    _redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connected")
except Exception:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available — running without cache")

QUOTE_TTL = 120   # 2 minutes for quote caching
HISTORY_TTL = 1800  # 30 minutes


class MarketService:

    def _redis_get(self, key: str) -> Optional[dict]:
        if not REDIS_AVAILABLE:
            return None
        try:
            val = _redis_client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    def _redis_set(self, key: str, data: dict, ttl: int):
        if not REDIS_AVAILABLE:
            return
        try:
            _redis_client.setex(key, ttl, json.dumps(data, default=str))
        except Exception:
            pass

    def get_quote(self, symbol: str, db: Session, force_live: bool = False) -> Optional[QuoteResponse]:
        """Get quote: Redis → DB snapshot (if fresh) → live yfinance."""
        symbol = symbol.upper()
        cache_key = f"quote:{symbol}"

        if not force_live:
            cached = self._redis_get(cache_key)
            if cached:
                return QuoteResponse(**cached)

        stock = db.query(Stock).filter(Stock.symbol == symbol).first()

        # Check recent DB snapshot (last 5 min) if not forcing live fetch
        if stock and not force_live:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
            snap = (
                db.query(MarketSnapshot)
                .filter(
                    MarketSnapshot.stock_id == stock.id,
                    MarketSnapshot.collected_at >= cutoff,
                )
                .order_by(MarketSnapshot.collected_at.desc())
                .first()
            )
            if snap:
                q = QuoteResponse(
                    symbol=symbol,
                    company_name=stock.company_name,
                    price=snap.price,
                    open=snap.open,
                    high=snap.high,
                    low=snap.low,
                    previous_close=snap.previous_close,
                    volume=snap.volume,
                    change_pct=snap.change_pct,
                    market_cap=snap.market_cap,
                    timestamp=snap.timestamp,
                    data_status=snap.data_status,
                    sector=stock.sector,
                )
                self._redis_set(cache_key, q.model_dump(), QUOTE_TTL)
                return q

        # Fetch live quote
        raw = yfinance_provider.get_quote(symbol)
        if not raw:
            # Fallback to latest snapshot in DB if yfinance rate limited
            if stock:
                latest_snap = (
                    db.query(MarketSnapshot)
                    .filter(MarketSnapshot.stock_id == stock.id)
                    .order_by(MarketSnapshot.collected_at.desc())
                    .first()
                )
                if latest_snap:
                    return QuoteResponse(
                        symbol=symbol,
                        company_name=stock.company_name,
                        price=latest_snap.price,
                        open=latest_snap.open,
                        high=latest_snap.high,
                        low=latest_snap.low,
                        previous_close=latest_snap.previous_close,
                        volume=latest_snap.volume,
                        change_pct=latest_snap.change_pct,
                        market_cap=latest_snap.market_cap,
                        timestamp=latest_snap.timestamp,
                        data_status=latest_snap.data_status,
                        sector=stock.sector,
                    )
            return None

        # Save snapshot
        if stock:
            snap = MarketSnapshot(
                stock_id=stock.id,
                price=raw["price"],
                open=raw.get("open"),
                high=raw.get("high"),
                low=raw.get("low"),
                previous_close=raw.get("previous_close"),
                volume=raw.get("volume"),
                market_cap=raw.get("market_cap"),
                change_pct=raw.get("change_pct"),
                timestamp=raw["timestamp"],
                source=raw["source"],
                data_status=raw["data_status"],
            )
            db.add(snap)
            db.commit()

        q = QuoteResponse(
            symbol=symbol,
            company_name=stock.company_name if stock else symbol,
            price=raw["price"],
            open=raw.get("open"),
            high=raw.get("high"),
            low=raw.get("low"),
            previous_close=raw.get("previous_close"),
            volume=raw.get("volume"),
            change_pct=raw.get("change_pct"),
            market_cap=raw.get("market_cap"),
            timestamp=raw["timestamp"],
            data_status=raw["data_status"],
            sector=stock.sector if stock else None,
        )
        self._redis_set(cache_key, q.model_dump(), QUOTE_TTL)
        return q

    def sync_live_quotes_for_stocks(self, stocks: List[Stock], db: Session) -> Dict[str, dict]:
        """Batch sync live quotes from yfinance and save MarketSnapshots to DB."""
        if not stocks:
            return {}

        symbols = [s.symbol for s in stocks]
        batch = yfinance_provider.get_batch_quotes(symbols)
        now = datetime.now(timezone.utc)

        for stock in stocks:
            raw = batch.get(stock.symbol)
            if raw and raw.get("price"):
                snap = MarketSnapshot(
                    stock_id=stock.id,
                    price=raw["price"],
                    open=raw.get("open"),
                    high=raw.get("high"),
                    low=raw.get("low"),
                    previous_close=raw.get("previous_close"),
                    volume=raw.get("volume"),
                    market_cap=raw.get("market_cap"),
                    change_pct=raw.get("change_pct"),
                    timestamp=now,
                    source="yfinance",
                    data_status="LIVE",
                )
                db.add(snap)
                # Update Redis
                cache_key = f"quote:{stock.symbol}"
                q = QuoteResponse(
                    symbol=stock.symbol,
                    company_name=stock.company_name,
                    price=raw["price"],
                    open=raw.get("open"),
                    high=raw.get("high"),
                    low=raw.get("low"),
                    previous_close=raw.get("previous_close"),
                    volume=raw.get("volume"),
                    change_pct=raw.get("change_pct"),
                    market_cap=raw.get("market_cap"),
                    timestamp=now,
                    data_status="LIVE",
                    sector=stock.sector,
                )
                self._redis_set(cache_key, q.model_dump(), QUOTE_TTL)

        db.commit()
        return batch

    def get_history(self, symbol: str, days: int = 30) -> List[HistoryPoint]:
        """Fetch OHLCV history with Redis caching."""
        cache_key = f"history:{symbol}:{days}"
        cached = self._redis_get(cache_key)
        if cached:
            return [HistoryPoint(**p) for p in cached]

        raw = yfinance_provider.get_history(symbol, days)
        points = [HistoryPoint(**p) for p in raw]
        self._redis_set(cache_key, raw, HISTORY_TTL)
        return points

    def refresh_all_quotes(self, db: Session):
        """Background worker: refresh quotes for all tracked stocks."""
        stocks = db.query(Stock).all()
        if stocks:
            self.sync_live_quotes_for_stocks(stocks, db)


market_service = MarketService()
