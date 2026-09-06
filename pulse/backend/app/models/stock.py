from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    exchange = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    sector_etf = Column(String, nullable=True)  # e.g. XLK for tech
    currency = Column(String, default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
