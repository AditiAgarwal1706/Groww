from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class StockBase(BaseModel):
    symbol: str
    company_name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    currency: str = "USD"


class StockResponse(StockBase):
    id: int

    class Config:
        from_attributes = True


class QuoteResponse(BaseModel):
    symbol: str
    company_name: str
    price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    volume: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime
    data_status: str = "LIVE"
    sector: Optional[str] = None


class HistoryPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoryResponse(BaseModel):
    symbol: str
    history: list[HistoryPoint]
