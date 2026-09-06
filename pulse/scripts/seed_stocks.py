"""
Stock seeder — adds common stocks to the database from yfinance with fallback metadata.
Run this to populate the stocks table.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.db.database import Base, engine
from app.db.session import SessionLocal
from app.models.stock import Stock
from app.services.market.provider import yfinance_provider
import time

SYMBOLS = [
    "NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "META", "AMZN", "AMD",
    "NFLX", "INTC", "CRM", "ORCL", "QCOM", "AVGO", "TSM",
    "JPM", "BAC", "GS", "MS", "V", "MA", "PYPL",
    "JNJ", "PFE", "UNH", "ABBV", "MRK",
    "XOM", "CVX", "SHEL", "BP",
    "SPY", "QQQ", "XLK", "XLY", "XLF", "XLE", "XLV",
]

DEFAULT_METADATA = {
    "NVDA": {"company_name": "NVIDIA Corporation", "sector": "Technology", "sector_etf": "XLK"},
    "TSLA": {"company_name": "Tesla, Inc.", "sector": "Consumer Cyclical", "sector_etf": "XLY"},
    "AAPL": {"company_name": "Apple Inc.", "sector": "Technology", "sector_etf": "XLK"},
    "MSFT": {"company_name": "Microsoft Corporation", "sector": "Technology", "sector_etf": "XLK"},
    "GOOGL": {"company_name": "Alphabet Inc.", "sector": "Communication Services", "sector_etf": "XLC"},
    "META": {"company_name": "Meta Platforms, Inc.", "sector": "Communication Services", "sector_etf": "XLC"},
    "AMZN": {"company_name": "Amazon.com, Inc.", "sector": "Consumer Cyclical", "sector_etf": "XLY"},
    "AMD": {"company_name": "Advanced Micro Devices, Inc.", "sector": "Technology", "sector_etf": "XLK"},
    "NFLX": {"company_name": "Netflix, Inc.", "sector": "Communication Services", "sector_etf": "XLC"},
    "INTC": {"company_name": "Intel Corporation", "sector": "Technology", "sector_etf": "XLK"},
    "CRM": {"company_name": "Salesforce, Inc.", "sector": "Technology", "sector_etf": "XLK"},
    "ORCL": {"company_name": "Oracle Corporation", "sector": "Technology", "sector_etf": "XLK"},
    "QCOM": {"company_name": "QUALCOMM Incorporated", "sector": "Technology", "sector_etf": "XLK"},
    "AVGO": {"company_name": "Broadcom Inc.", "sector": "Technology", "sector_etf": "XLK"},
    "TSM": {"company_name": "Taiwan Semiconductor Manufacturing Co.", "sector": "Technology", "sector_etf": "XLK"},
    "JPM": {"company_name": "JPMorgan Chase & Co.", "sector": "Financial Services", "sector_etf": "XLF"},
    "BAC": {"company_name": "Bank of America Corporation", "sector": "Financial Services", "sector_etf": "XLF"},
    "GS": {"company_name": "The Goldman Sachs Group, Inc.", "sector": "Financial Services", "sector_etf": "XLF"},
    "MS": {"company_name": "Morgan Stanley", "sector": "Financial Services", "sector_etf": "XLF"},
    "V": {"company_name": "Visa Inc.", "sector": "Financial Services", "sector_etf": "XLF"},
    "MA": {"company_name": "Mastercard Incorporated", "sector": "Financial Services", "sector_etf": "XLF"},
    "PYPL": {"company_name": "PayPal Holdings, Inc.", "sector": "Financial Services", "sector_etf": "XLF"},
    "JNJ": {"company_name": "Johnson & Johnson", "sector": "Healthcare", "sector_etf": "XLV"},
    "PFE": {"company_name": "Pfizer Inc.", "sector": "Healthcare", "sector_etf": "XLV"},
    "UNH": {"company_name": "UnitedHealth Group Incorporated", "sector": "Healthcare", "sector_etf": "XLV"},
    "ABBV": {"company_name": "AbbVie Inc.", "sector": "Healthcare", "sector_etf": "XLV"},
    "MRK": {"company_name": "Merck & Co., Inc.", "sector": "Healthcare", "sector_etf": "XLV"},
    "XOM": {"company_name": "Exxon Mobil Corporation", "sector": "Energy", "sector_etf": "XLE"},
    "CVX": {"company_name": "Chevron Corporation", "sector": "Energy", "sector_etf": "XLE"},
    "SHEL": {"company_name": "Shell plc", "sector": "Energy", "sector_etf": "XLE"},
    "BP": {"company_name": "BP p.l.c.", "sector": "Energy", "sector_etf": "XLE"},
    "SPY": {"company_name": "SPDR S&P 500 ETF Trust", "sector": "Index ETF", "sector_etf": "SPY"},
    "QQQ": {"company_name": "Invesco QQQ Trust", "sector": "Index ETF", "sector_etf": "QQQ"},
    "XLK": {"company_name": "Technology Select Sector SPDR Fund", "sector": "Sector ETF", "sector_etf": "XLK"},
    "XLY": {"company_name": "Consumer Discretionary Select Sector SPDR Fund", "sector": "Sector ETF", "sector_etf": "XLY"},
    "XLF": {"company_name": "Financial Select Sector SPDR Fund", "sector": "Sector ETF", "sector_etf": "XLF"},
    "XLE": {"company_name": "Energy Select Sector SPDR Fund", "sector": "Sector ETF", "sector_etf": "XLE"},
    "XLV": {"company_name": "Health Care Select Sector SPDR Fund", "sector": "Sector ETF", "sector_etf": "XLV"},
}

def seed_stocks():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added = 0
    try:
        for symbol in SYMBOLS:
            existing = db.query(Stock).filter(Stock.symbol == symbol).first()
            if existing:
                print(f"  [EXISTS] {symbol}")
                continue
            
            info = DEFAULT_METADATA.get(symbol, {"company_name": f"{symbol} Inc.", "sector": "General", "sector_etf": "SPY"})
            try:
                live_info = yfinance_provider.get_company_info(symbol)
                if live_info and live_info.get("company_name"):
                    info = live_info
            except Exception:
                pass
                
            stock = Stock(
                symbol=symbol,
                company_name=info["company_name"],
                exchange=info.get("exchange", "NASDAQ"),
                sector=info.get("sector"),
                sector_etf=info.get("sector_etf", "SPY"),
                currency=info.get("currency", "USD"),
            )
            db.add(stock)
            db.commit()
            print(f"  [ADDED] {symbol} - {info['company_name']}")
            added += 1
            time.sleep(0.1)
        print(f"\n[OK] Added {added} new stocks ({len(SYMBOLS)} total)")
    finally:
        db.close()

if __name__ == "__main__":
    seed_stocks()
