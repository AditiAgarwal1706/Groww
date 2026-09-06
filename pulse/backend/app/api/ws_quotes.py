"""
WebSocket endpoint for real-time quote streaming.
Clients connect with their JWT token and a watchlist_id.
Every PUSH_INTERVAL seconds the server fetches fresh quotes and broadcasts them.
"""
import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.services.market.provider import yfinance_provider

router = APIRouter()
logger = logging.getLogger(__name__)

PUSH_INTERVAL = 15  # seconds between price pushes


def _decode_token(token: str) -> Optional[int]:
    """Decode JWT and return user_id, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except (JWTError, ValueError, TypeError):
        return None


def _get_watchlist_symbols(watchlist_id: int, user_id: int) -> list[str]:
    """Get stock symbols for a watchlist. Returns [] if not found / not owned."""
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


@router.websocket("/ws/quotes")
async def ws_quotes(
    websocket: WebSocket,
    token: str = Query(...),
    watchlist_id: int = Query(...),
):
    """
    WebSocket that pushes real-time quotes for all stocks in a watchlist.
    Connect with: ws://localhost:8000/ws/quotes?token=JWT&watchlist_id=1
    """
    # Authenticate
    user_id = _decode_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    logger.info(f"WS quotes: user={user_id} watchlist={watchlist_id} connected")

    try:
        while True:
            # Fetch watchlist symbols on every loop (handles additions/removals)
            symbols = await asyncio.to_thread(
                _get_watchlist_symbols, watchlist_id, user_id
            )

            if symbols:
                # Fetch live quotes in a thread (yfinance is blocking)
                quotes = await asyncio.to_thread(
                    yfinance_provider.get_batch_quotes, symbols
                )

                if quotes:
                    payload = {
                        "type": "quotes",
                        "data": {
                            symbol: {
                                "symbol": q["symbol"],
                                "price": q["price"],
                                "change_pct": q.get("change_pct"),
                                "volume": q.get("volume"),
                                "open": q.get("open"),
                                "high": q.get("high"),
                                "low": q.get("low"),
                                "previous_close": q.get("previous_close"),
                                "timestamp": q["timestamp"].isoformat() if hasattr(q.get("timestamp"), "isoformat") else str(q.get("timestamp")),
                                "data_status": q.get("data_status", "LIVE"),
                            }
                            for symbol, q in quotes.items()
                        },
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                    await websocket.send_text(json.dumps(payload))
                    logger.debug(f"WS quotes: pushed {len(quotes)} quotes to user={user_id}")
            else:
                # Empty watchlist — send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat"}))

            await asyncio.sleep(PUSH_INTERVAL)

    except WebSocketDisconnect:
        logger.info(f"WS quotes: user={user_id} watchlist={watchlist_id} disconnected")
    except Exception as e:
        logger.error(f"WS quotes error for user={user_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Server error")
        except Exception:
            pass
