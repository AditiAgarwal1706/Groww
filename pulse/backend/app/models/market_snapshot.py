from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from app.db.database import Base


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    previous_close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)  # vs previous close
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(String, default="yfinance")
    data_status = Column(String, default="LIVE")  # LIVE, DELAYED, STALE, UNAVAILABLE
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
