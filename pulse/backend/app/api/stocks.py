from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.schemas.stock import StockResponse, QuoteResponse, HistoryResponse, HistoryPoint
from app.services.market.service import market_service
from app.services.market.provider import yfinance_provider
import logging

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
logger = logging.getLogger(__name__)


@router.get("/search", response_model=List[StockResponse])
def search_stocks(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Search stocks by symbol or name. Auto-fetches real world symbols from yfinance if not in DB."""
    q_clean = q.strip()
    results = db.query(Stock).filter(
        (Stock.symbol.ilike(f"%{q_clean}%")) | (Stock.company_name.ilike(f"%{q_clean}%"))
    ).limit(20).all()

    # If symbol search returns no exact match and query is short (likely a stock ticker like TSLA, AAPL, BTC-USD, etc.)
    symbol_upper = q_clean.upper()
    exact_match = any(s.symbol == symbol_upper for s in results)

    if not exact_match and len(q_clean) <= 12 and q_clean.isalnum() or "-" in q_clean or "." in q_clean:
        try:
            info = yfinance_provider.get_company_info(symbol_upper)
            if info and info.get("company_name") and info["company_name"] != symbol_upper:
                # Check if stock exists by exact symbol
                existing = db.query(Stock).filter(Stock.symbol == symbol_upper).first()
                if not existing:
                    new_stock = Stock(
                        symbol=symbol_upper,
                        company_name=info["company_name"],
                        exchange=info.get("exchange", "NASDAQ"),
                        sector=info.get("sector"),
                        sector_etf=info.get("sector_etf", "SPY"),
                        currency=info.get("currency", "USD"),
                    )
                    db.add(new_stock)
                    db.commit()
                    db.refresh(new_stock)
                    results.insert(0, new_stock)
        except Exception as e:
            logger.debug(f"Dynamic stock lookup skipped for {symbol_upper}: {e}")

    return results


@router.get("/{symbol}/quote", response_model=QuoteResponse)
def get_quote(
    symbol: str,
    sync_live: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    symbol = symbol.upper()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()

    # If stock not in DB yet, try fetching company info & adding it
    if not stock:
        info = yfinance_provider.get_company_info(symbol)
        stock = Stock(
            symbol=symbol,
            company_name=info.get("company_name", symbol),
            exchange=info.get("exchange", "US"),
            sector=info.get("sector"),
            sector_etf=info.get("sector_etf", "SPY"),
            currency=info.get("currency", "USD"),
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

    quote = market_service.get_quote(symbol, db, force_live=sync_live)
    if not quote:
        raise HTTPException(status_code=503, detail="Market data unavailable for symbol")
    return quote


@router.get("/{symbol}/history", response_model=HistoryResponse)
def get_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    _: User = Depends(get_current_user),
):
    symbol = symbol.upper()
    history = market_service.get_history(symbol, days)
    return HistoryResponse(symbol=symbol, history=history)
