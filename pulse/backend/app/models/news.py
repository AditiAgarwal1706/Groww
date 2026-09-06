from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from app.db.database import Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    url = Column(String, nullable=True, unique=True)
    url_hash = Column(String, nullable=True, unique=True, index=True)  # for dedup
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sentiment = Column(String, nullable=True)   # POSITIVE, NEGATIVE, NEUTRAL
    impact_score = Column(Float, default=0.5)   # 0.0 – 1.0
    event_type = Column(String, nullable=True)  # EARNINGS, REGULATORY, etc.
    collected_at = Column(DateTime(timezone=True), nullable=True)
