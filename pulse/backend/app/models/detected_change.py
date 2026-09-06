from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from app.db.database import Base


class DetectedChange(Base):
    __tablename__ = "detected_changes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String, nullable=False)  # PRICE, VOLUME, NEWS, SECTOR, COMPOSITE
    severity = Column(String, nullable=False)      # NORMAL, WATCH, IMPORTANT, MAJOR
    score = Column(Float, nullable=False)
    summary = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)         # JSON string of evidence payload
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
