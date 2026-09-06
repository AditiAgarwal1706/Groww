"""
PULSE — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from app.core.config import settings
from app.db.database import Base, engine
from app.api import auth, watchlists, stocks, changes, news, dashboard
from app.api import ws_quotes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PULSE backend...")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Start background workers
    from app.workers.market_worker import refresh_market_data, refresh_news

    scheduler.add_job(
        refresh_market_data,
        "interval",
        seconds=settings.MARKET_POLL_INTERVAL_SECONDS,
        id="market_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_news,
        "interval",
        seconds=settings.NEWS_POLL_INTERVAL_SECONDS,
        id="news_worker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background workers started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("PULSE backend shutting down")


app = FastAPI(
    title="PULSE — Smart Market Watchlist",
    description="An attention layer for financial markets",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(watchlists.router)
app.include_router(stocks.router)
app.include_router(changes.router)
app.include_router(news.router)
app.include_router(dashboard.router)
app.include_router(ws_quotes.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "PULSE"}


@app.get("/")
def root():
    return {
        "service": "PULSE Smart Market Watchlist",
        "version": "1.0.0",
        "tagline": "Your market. Your attention. Nothing unnecessary.",
    }
