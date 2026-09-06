from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.models.stock import Stock
from app.schemas.watchlist import (
    WatchlistCreate, WatchlistUpdate, WatchlistResponse,
    WatchlistDetailResponse, AddStockRequest
)
from app.services.market.service import market_service

router = APIRouter(prefix="/api/watchlists", tags=["watchlists"])


def _get_watchlist_or_404(watchlist_id: int, user_id: int, db: Session) -> Watchlist:
    wl = db.query(Watchlist).filter(
        Watchlist.id == watchlist_id, Watchlist.user_id == user_id
    ).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return wl


@router.get("", response_model=List[WatchlistResponse])
def list_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wls = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    result = []
    for wl in wls:
        count = db.query(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).count()
        result.append(WatchlistResponse(
            id=wl.id, name=wl.name,
            created_at=wl.created_at, updated_at=wl.updated_at,
            stock_count=count,
        ))
    return result


@router.post("", response_model=WatchlistResponse, status_code=201)
def create_watchlist(
    req: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = Watchlist(user_id=current_user.id, name=req.name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return WatchlistResponse(
        id=wl.id, name=wl.name,
        created_at=wl.created_at, updated_at=wl.updated_at,
        stock_count=0,
    )


@router.get("/{watchlist_id}", response_model=WatchlistDetailResponse)
def get_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = _get_watchlist_or_404(watchlist_id, current_user.id, db)
    stocks = db.query(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).all()
    return WatchlistDetailResponse(
        id=wl.id, name=wl.name,
        created_at=wl.created_at, updated_at=wl.updated_at,
        stock_count=len(stocks), stocks=stocks,
    )


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def update_watchlist(
    watchlist_id: int,
    req: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = _get_watchlist_or_404(watchlist_id, current_user.id, db)
    wl.name = req.name
    db.commit()
    db.refresh(wl)
    count = db.query(WatchlistStock).filter(WatchlistStock.watchlist_id == wl.id).count()
    return WatchlistResponse(
        id=wl.id, name=wl.name,
        created_at=wl.created_at, updated_at=wl.updated_at,
        stock_count=count,
    )


@router.delete("/{watchlist_id}", status_code=204)
def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = _get_watchlist_or_404(watchlist_id, current_user.id, db)
    db.delete(wl)
    db.commit()


@router.post("/{watchlist_id}/stocks", status_code=201)
def add_stock(
    watchlist_id: int,
    req: AddStockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = _get_watchlist_or_404(watchlist_id, current_user.id, db)
    symbol_upper = req.symbol.upper().strip()
    stock = db.query(Stock).filter(Stock.symbol == symbol_upper).first()

    if not stock:
        # Auto-register real stock from yfinance — validate it exists first
        from app.services.market.provider import yfinance_provider
        info = yfinance_provider.get_company_info(symbol_upper)
        company_name = info.get("company_name", "")

        # Reject if yfinance returns no real company name (symbol doesn't exist)
        if not company_name or company_name == symbol_upper:
            # Try fetching a quote as a secondary check
            quote = yfinance_provider.get_quote(symbol_upper)
            if not quote:
                raise HTTPException(
                    status_code=422,
                    detail=f"Symbol '{symbol_upper}' not found on any exchange. Please check the ticker (e.g. RELIANCE.NS for NSE, AAPL for NASDAQ)."
                )
            # Use symbol as company name if quote exists but info is limited
            company_name = symbol_upper

        stock = Stock(
            symbol=symbol_upper,
            company_name=company_name,
            exchange=info.get("exchange", "NASDAQ"),
            sector=info.get("sector"),
            sector_etf=info.get("sector_etf", "SPY"),
            currency=info.get("currency", "USD"),
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

    exists = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == wl.id,
        WatchlistStock.stock_id == stock.id,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"{stock.symbol} is already in your watchlist")

    ws = WatchlistStock(watchlist_id=wl.id, stock_id=stock.id)
    db.add(ws)
    db.commit()

    # Fetch live quote in background for newly added stock (best-effort)
    try:
        market_service.get_quote(symbol_upper, db, force_live=True)
    except Exception:
        pass  # Don't fail the add if quote fetch fails

    return {"message": f"{stock.symbol} added to {wl.name}"}


@router.delete("/{watchlist_id}/stocks/{symbol}", status_code=204)
def remove_stock(
    watchlist_id: int,
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = _get_watchlist_or_404(watchlist_id, current_user.id, db)
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    ws = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == wl.id,
        WatchlistStock.stock_id == stock.id,
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")
    db.delete(ws)
    db.commit()
