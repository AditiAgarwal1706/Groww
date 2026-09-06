"""
Background market data worker.
Runs on APScheduler — fetches quotes for all tracked stocks every 5 min.
"""
import logging
from app.services.market.service import market_service
from app.services.news.provider import news_provider
from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.news import News

logger = logging.getLogger(__name__)


def refresh_market_data():
    """Refresh quotes for all tracked stocks."""
    db = SessionLocal()
    try:
        stocks = db.query(Stock).all()
        logger.info(f"Market worker: refreshing {len(stocks)} stocks")
        market_service.refresh_all_quotes(db)
    except Exception as e:
        logger.error(f"Market worker error: {e}")
    finally:
        db.close()


def refresh_news():
    """Fetch latest news for all tracked stocks."""
    db = SessionLocal()
    try:
        stocks = db.query(Stock).all()
        for stock in stocks:
            try:
                articles = news_provider.fetch_news(stock.symbol, stock.company_name, days_back=2)
                for art in articles:
                    # Skip if already exists
                    if db.query(News).filter(News.url_hash == art["url_hash"]).first():
                        continue
                    news = News(
                        stock_id=stock.id,
                        title=art["title"],
                        summary=art.get("summary"),
                        source=art.get("source"),
                        url=art.get("url"),
                        url_hash=art.get("url_hash"),
                        published_at=art["published_at"],
                        sentiment=art.get("sentiment"),
                        impact_score=art.get("impact_score", 0.5),
                        event_type=art.get("event_type"),
                    )
                    db.add(news)
                db.commit()
            except Exception as e:
                logger.error(f"News refresh error for {stock.symbol}: {e}")
    except Exception as e:
        logger.error(f"News worker error: {e}")
    finally:
        db.close()
