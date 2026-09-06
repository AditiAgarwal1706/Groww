"""
Pytest configuration and shared fixtures for PULSE backend test suite.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base
from app.db.session import get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.models.market_snapshot import MarketSnapshot


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory database session for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Fixture providing a test user."""
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("Password123!"),
        name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user



@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Authorization headers for authenticated client requests."""
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}", "token": token}



@pytest.fixture(scope="function")
def test_stock(db_session):
    """Fixture providing a sample stock symbol."""
    stock = Stock(
        symbol="NVDA",
        company_name="NVIDIA Corporation",
        exchange="NASDAQ",
        sector="Technology",
        sector_etf="XLK",
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


@pytest.fixture(scope="function")
def test_watchlist(db_session, test_user, test_stock):
    """Fixture providing a watchlist containing a stock."""
    wl = Watchlist(name="Tech Watchlist", user_id=test_user.id)
    db_session.add(wl)
    db_session.commit()
    db_session.refresh(wl)

    ws = WatchlistStock(watchlist_id=wl.id, stock_id=test_stock.id)
    db_session.add(ws)

    snap = MarketSnapshot(

        stock_id=test_stock.id,
        price=125.50,
        open=124.00,
        high=127.00,
        low=123.50,
        previous_close=124.00,
        volume=50_000_000,
        change_pct=1.21,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(snap)

    db_session.commit()
    return wl

