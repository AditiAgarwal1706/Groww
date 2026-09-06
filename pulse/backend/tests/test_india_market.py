"""
Tests for Indian market support (NSE/BSE, INR currency, NIFTY 50 benchmark attribution).
"""
from app.services.market.provider import YFinanceProvider
from app.models.stock import Stock


def test_company_info_indian_nse():
    provider = YFinanceProvider()
    info = provider.get_company_info("RELIANCE.NS")
    
    assert info["currency"] == "INR"
    assert info["exchange"] == "NSE"
    assert info["sector_etf"] in ["^NSEI", "XLK", "XLE"] or info["sector_etf"] is not None


def test_company_info_indian_bse():
    provider = YFinanceProvider()
    info = provider.get_company_info("TCS.BO")
    
    assert info["currency"] == "INR"
    assert info["exchange"] == "BSE"


def test_company_info_us_stock():
    provider = YFinanceProvider()
    info = provider.get_company_info("AAPL")
    
    assert info["currency"] == "USD"
    assert info["exchange"] in ["NASDAQ", "US", "NMS"]


def test_indian_stocks_db_model(db_session):
    rel_stock = Stock(
        symbol="RELIANCE.NS",
        company_name="Reliance Industries Limited",
        exchange="NSE",
        sector="Energy",
        sector_etf="^NSEI"
    )
    tcs_stock = Stock(
        symbol="TCS.NS",
        company_name="Tata Consultancy Services",
        exchange="NSE",
        sector="Technology",
        sector_etf="^NSEI"
    )
    db_session.add(rel_stock)
    db_session.add(tcs_stock)
    db_session.commit()

    fetched = db_session.query(Stock).filter(Stock.symbol.in_(["RELIANCE.NS", "TCS.NS"])).all()
    assert len(fetched) == 2
    symbols = [s.symbol for s in fetched]
    assert "RELIANCE.NS" in symbols
    assert "TCS.NS" in symbols
