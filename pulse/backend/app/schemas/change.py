from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class ChangeSignal(BaseModel):
    type: str     # PRICE, VOLUME, NEWS, SECTOR, MARKET
    value: float
    label: str


class AttributionResponse(BaseModel):
    company_specific: float   # 0.0–1.0
    sector_effect: float
    market_effect: float
    company_specific_pct: float  # as percentage
    sector_effect_pct: float
    market_effect_pct: float


class DetectedChangeResponse(BaseModel):
    id: int
    symbol: str
    company_name: str
    severity: str           # NORMAL, WATCH, IMPORTANT, MAJOR
    attention_score: float  # 0–100
    price: float
    change_pct: Optional[float]
    volume_ratio: Optional[float]
    signals: List[ChangeSignal]
    summary: str
    detected_at: datetime

    class Config:
        from_attributes = True


class ChangeSummary(BaseModel):
    major: int
    important: int
    watch: int
    normal: int
    total: int


class AnalysisResponse(BaseModel):
    symbol: str
    company_name: str
    attention_score: float
    severity: str
    price_z_score: float
    volume_ratio: float
    attribution: AttributionResponse
    signals: List[ChangeSignal]
    confidence: int


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str  # NEWS, PRICE_MOVE, VOLUME_SPIKE, SECTOR_MOVE
    description: str
    severity: Optional[str] = None


class AIExplanation(BaseModel):
    summary: str
    drivers: List[Dict[str, Any]]
    confidence: int
    caveat: str


class RangeEvent(BaseModel):
    date: str
    event: str
    impact: str  # POSITIVE, NEGATIVE, NEUTRAL


class RangeAnalysisResponse(BaseModel):
    symbol: str
    company_name: str
    currency: str
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    price_change: float
    price_change_pct: float
    high_price: float
    low_price: float
    news_count: int
    ai_explanation: Dict[str, Any]
    key_events: List[RangeEvent]
    news_articles: List[Dict[str, Any]]



class DashboardStock(BaseModel):
    symbol: str
    company_name: str
    price: float
    change_pct: Optional[float]
    attention_score: float
    severity: str
    volume_ratio: Optional[float]
    data_status: str


class DashboardResponse(BaseModel):
    last_checked_at: Optional[datetime]
    summary: ChangeSummary
    top_attention: List[DetectedChangeResponse]
    watchlist: List[DashboardStock]
    watchlist_id: Optional[int]
    watchlist_name: Optional[str]
