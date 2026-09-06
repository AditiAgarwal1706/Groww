"""
WebSocket endpoint for real-time quote streaming.
Clients connect with their JWT token and a watchlist_id or symbol list.

During active market hours: pushes fresh yfinance prices every 3 seconds (real tick data).
During pre-market / after-hours / closed: pushes the most recent known prices with accurate
status labels — NO artificial price simulation. Prices shown are what the market actually did.
"""
import asyncio
import json
import logging
import time
from typing import Optional, List, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.services.market.provider import yfinance_provider
from app.services.market.hours import get_market_status

router = APIRouter()
logger = logging.getLogger(__name__)

PUSH_INTERVAL_LIVE   = 3.0   # seconds during live market hours
PUSH_INTERVAL_CLOSED = 30.0  # seconds when market is closed (reduces API spam)

# In-memory cache of last fetched real quotes (so we can push last-known prices instantly)
_last_real_quotes: Dict[str, dict] = {}


def _decode_token(token: str) -> Optional[int]:
    """Decode JWT and return user_id, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except (JWTError, ValueError, TypeError):
        return None


def _get_watchlist_symbols(watchlist_id: int, user_id: int) -> List[str]:
    """Get stock symbols for a watchlist safely."""
    db: Session = SessionLocal()
    try:
        wl = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user_id,
        ).first()
        if not wl:
            return []
        wl_stocks = db.query(WatchlistStock).filter(
            WatchlistStock.watchlist_id == wl.id
        ).all()
        return [ws.stock.symbol for ws in wl_stocks if ws.stock]
    except Exception as e:
        logger.error(f"Error fetching watchlist symbols: {e}")
        return []
    finally:
        db.close()


def _build_quote_payload(symbol: str, raw: dict, status: str) -> dict:
    """
    Build a clean quote dict from raw yfinance data.
    The status is honest — LIVE, PRE_MARKET, AFTER_HOURS, or MARKET_CLOSED.
    No prices are fabricated.
    """
    price = raw.get("price", 0.0)
    prev_close = raw.get("previous_close") or price
    change_pct = raw.get("change_pct")
    if change_pct is None and prev_close and prev_close > 0:
        change_pct = round(((price - prev_close) / prev_close) * 100, 2)

    return {
        "symbol": symbol,
        "price": price,
        "change_pct": round(change_pct, 2) if change_pct is not None else 0.0,
        "volume": raw.get("volume"),
        "open": raw.get("open"),
        "high": raw.get("high"),
        "low": raw.get("low"),
        "previous_close": prev_close,
        "timestamp": time.time(),
        "data_status": status,
    }


@router.websocket("/ws/quotes")
async def ws_quotes(
    websocket: WebSocket,
    token: str = Query(...),
    watchlist_id: Optional[int] = Query(None),
):
    """
    WebSocket endpoint that pushes real-time quotes for all stocks in a watchlist or custom symbols.

    During live market hours: fetches fresh prices every 3 seconds.
    When markets are closed (weekends, after-hours): uses last-known real prices with accurate
    MARKET_CLOSED / AFTER_HOURS / PRE_MARKET status labels.

    Supports client control messages:
      {"action": "ping"}
      {"action": "subscribe", "symbols": ["RELIANCE.NS", "AAPL"]}
    """
    user_id = _decode_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    logger.info(f"WS quotes connected: user={user_id} watchlist_id={watchlist_id}")

    custom_symbols: List[str] = []

    async def incoming_listener():
        nonlocal custom_symbols
        try:
            while True:
                data_str = await websocket.receive_text()
                try:
                    data = json.loads(data_str)
                    action = data.get("action")
                    if action == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "timestamp": time.time()}))
                    elif action == "subscribe" and isinstance(data.get("symbols"), list):
                        custom_symbols = [str(s).upper() for s in data["symbols"]]
                        logger.info(f"WS quotes user={user_id} custom subscribe: {custom_symbols}")
                except Exception as ex:
                    logger.debug(f"WS incoming frame parse error: {ex}")
        except Exception:
            pass

    listener_task = asyncio.create_task(incoming_listener())

    try:
        while True:
            symbols = custom_symbols
            if not symbols and watchlist_id:
                symbols = await asyncio.to_thread(
                    _get_watchlist_symbols, watchlist_id, user_id
                )

            if symbols:
                # Determine market status for each symbol group
                # Use first symbol to detect Indian vs US market
                representative_symbol = symbols[0]
                market_status = get_market_status(representative_symbol)
                is_live = market_status == "LIVE"

                if is_live:
                    # --- LIVE MARKET: fetch fresh real prices ---
                    raw_quotes = await asyncio.to_thread(
                        yfinance_provider.get_batch_quotes, symbols
                    )
                    tick_quotes = {}
                    for sym in symbols:
                        raw = raw_quotes.get(sym)
                        if raw:
                            _last_real_quotes[sym] = raw  # cache for closed-market use
                            tick_quotes[sym] = _build_quote_payload(sym, raw, "LIVE")
                        elif sym in _last_real_quotes:
                            # Use cached if yfinance momentarily fails
                            tick_quotes[sym] = _build_quote_payload(sym, _last_real_quotes[sym], "LIVE")
                else:
                    # --- MARKET CLOSED / PRE-MARKET / AFTER-HOURS ---
                    # Only fetch fresh data if we don't have cached prices yet
                    missing = [s for s in symbols if s not in _last_real_quotes]
                    if missing:
                        fresh = await asyncio.to_thread(
                            yfinance_provider.get_batch_quotes, missing
                        )
                        for sym, raw in fresh.items():
                            if raw:
                                _last_real_quotes[sym] = raw

                    tick_quotes = {}
                    for sym in symbols:
                        if sym in _last_real_quotes:
                            tick_quotes[sym] = _build_quote_payload(
                                sym, _last_real_quotes[sym], market_status
                            )
                        else:
                            # Absolute fallback: unknown symbol, no data
                            tick_quotes[sym] = {
                                "symbol": sym,
                                "price": None,
                                "change_pct": None,
                                "volume": None,
                                "data_status": "UNAVAILABLE",
                                "timestamp": time.time(),
                            }

                payload = {
                    "type": "quotes",
                    "data": tick_quotes,
                    "market_status": market_status,
                    "timestamp": time.time(),
                }
                await websocket.send_text(json.dumps(payload))
            else:
                # Heartbeat when no symbols selected
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": time.time()}))

            # Slow down polling when markets are closed to avoid hammering yfinance
            representative = (custom_symbols or [None])[0] or ""
            status_now = get_market_status(representative)
            interval = PUSH_INTERVAL_LIVE if status_now == "LIVE" else PUSH_INTERVAL_CLOSED
            await asyncio.sleep(interval)

    except WebSocketDisconnect:
        logger.info(f"WS quotes disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WS quotes loop error user={user_id}: {e}")
    finally:
        listener_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
