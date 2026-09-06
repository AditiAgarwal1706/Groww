from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.stock import StockResponse


class WatchlistCreate(BaseModel):
    name: str


class WatchlistUpdate(BaseModel):
    name: str


class AddStockRequest(BaseModel):
    symbol: str


class WatchlistStockResponse(BaseModel):
    id: int
    stock: StockResponse
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    stock_count: int = 0

    class Config:
        from_attributes = True


class WatchlistDetailResponse(WatchlistResponse):
    stocks: List[WatchlistStockResponse] = []
