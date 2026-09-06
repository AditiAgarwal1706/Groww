from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.models.news import News
from app.schemas.news import NewsResponse

router = APIRouter(prefix="/api/stocks", tags=["news"])


@router.get("/{symbol}/news", response_model=List[NewsResponse])
def get_news(
    symbol: str,
    days: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles = (
        db.query(News)
        .filter(News.stock_id == stock.id, News.published_at >= cutoff)
        .order_by(News.published_at.desc())
        .limit(20)
        .all()
    )
    return articles
