from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NewsResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    source: Optional[str]
    url: Optional[str]
    published_at: datetime
    sentiment: Optional[str]
    impact_score: float
    event_type: Optional[str]

    class Config:
        from_attributes = True
