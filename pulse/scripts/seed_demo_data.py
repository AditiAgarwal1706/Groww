"""
PULSE Demo Data Seeder
======================
Creates a deterministic demo scenario that ALWAYS works during the hackathon demo.

Demo account: demo@pulse.app / Demo@2026!
Watchlist: "Tech Portfolio" with NVDA, TSLA, AAPL, MSFT, GOOGL, META, AMZN, AMD

The demo scenario shows:
- NVDA: -5.2% (MAJOR — Attention 92) — regulatory news + volume spike
- TSLA: +6.1% (MAJOR — Attention 81) — earnings beat
- AAPL: Earnings upcoming (IMPORTANT — Attention 67)
- Others: Normal (Attention < 30)
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from datetime import datetime, timezone, timedelta
import json

from app.db.database import Base, engine
from app.db.session import SessionLocal
from app.models.user import User
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.models.watchlist_stock import WatchlistStock
from app.models.market_snapshot import MarketSnapshot
from app.models.checkpoint import Checkpoint
from app.models.news import News
from app.models.detected_change import DetectedChange
from app.core.security import hash_password

# ── Demo Stocks ──────────────────────────────────────────────────────────────
DEMO_STOCKS = [
    {"symbol": "RELIANCE.NS", "company_name": "Reliance Industries Ltd", "sector": "Energy", "sector_etf": "^NSEI", "exchange": "NSE", "currency": "INR"},
    {"symbol": "TCS.NS",      "company_name": "Tata Consultancy Services", "sector": "Technology", "sector_etf": "^NSEI", "exchange": "NSE", "currency": "INR"},
    {"symbol": "INFY.NS",     "company_name": "Infosys Limited", "sector": "Technology", "sector_etf": "^NSEI", "exchange": "NSE", "currency": "INR"},
    {"symbol": "HDFCBANK.NS", "company_name": "HDFC Bank Limited", "sector": "Financials", "sector_etf": "^NSEI", "exchange": "NSE", "currency": "INR"},
    {"symbol": "TATAMOTORS.NS","company_name": "Tata Motors Limited", "sector": "Consumer Discretionary", "sector_etf": "^NSEI", "exchange": "NSE", "currency": "INR"},
    {"symbol": "NVDA", "company_name": "NVIDIA Corporation",        "sector": "Technology",    "sector_etf": "XLK", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "TSLA", "company_name": "Tesla, Inc.",                "sector": "Consumer Discretionary", "sector_etf": "XLY", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "AAPL", "company_name": "Apple Inc.",                 "sector": "Technology",    "sector_etf": "XLK", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "MSFT", "company_name": "Microsoft Corporation",      "sector": "Technology",    "sector_etf": "XLK", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "GOOGL","company_name": "Alphabet Inc.",              "sector": "Communication Services", "sector_etf": "XLC", "exchange": "NASDAQ", "currency": "USD"},
]

# ── Checkpoint prices (what user "last saw") ─────────────────────────────────
CHECKPOINT_PRICES = {
    "RELIANCE.NS": 2980.50,
    "TCS.NS": 4150.00,
    "INFY.NS": 1820.00,
    "HDFCBANK.NS": 1640.00,
    "TATAMOTORS.NS": 985.00,
    "NVDA": 183.21,
    "TSLA": 321.40,
    "AAPL": 240.90,
    "MSFT": 415.30,
    "GOOGL": 182.75,
}

# ── Current "after events" prices ────────────────────────────────────────────
CURRENT_PRICES = {
    "RELIANCE.NS": 3120.00,  # +4.68% — MAJOR (New green energy deal)
    "TCS.NS": 4185.00,       # +0.84% — NORMAL
    "INFY.NS": 1745.00,      # -4.12% — IMPORTANT (Q3 margin guidance)
    "HDFCBANK.NS": 1645.00,  # +0.30% — NORMAL
    "TATAMOTORS.NS": 1045.00,# +6.09% — MAJOR (Record EV sales)
    "NVDA": 174.30,  # -5.2% — MAJOR
    "TSLA": 341.20,  # +6.1% — MAJOR
    "AAPL": 241.10,  # +0.08% — IMPORTANT (earnings approaching)
    "MSFT": 416.50,  # +0.3% — NORMAL
    "GOOGL": 183.20, # +0.2% — NORMAL
}

CURRENT_VOLUMES = {
    "RELIANCE.NS": 15_000_000,
    "TCS.NS": 2_500_000,
    "INFY.NS": 12_000_000,
    "HDFCBANK.NS": 8_000_000,
    "TATAMOTORS.NS": 25_000_000,
    "NVDA": 89_000_000,
    "TSLA": 65_000_000,
    "AAPL": 35_000_000,
    "MSFT": 22_000_000,
    "GOOGL":18_000_000,
}

DEMO_NEWS = [
    {
        "symbol": "RELIANCE.NS",
        "title": "Reliance Industries announces ₹75,000 crore expansion into Green Energy & AI Data Centers",
        "summary": "Mukesh Ambani announced a major investment in solar gigafactories and AI infrastructure across Gujarat.",
        "source": "Economic Times",
        "event_type": "STRATEGIC",
        "sentiment": "POSITIVE",
        "impact_score": 0.89,
        "published_ago_hours": 4,
    },
    {
        "symbol": "TATAMOTORS.NS",
        "title": "Tata Motors EV division crosses 150,000 unit milestone, exports surge 45%",
        "summary": "Tata Motors reported record quarterly electric vehicle sales led by Punch EV and Nexon EV.",
        "source": "Moneycontrol",
        "event_type": "SALES",
        "sentiment": "POSITIVE",
        "impact_score": 0.85,
        "published_ago_hours": 8,
    },
    {
        "symbol": "INFY.NS",
        "title": "Infosys revises FY26 margin guidance downwards amidst US tech spend slowdown",
        "summary": "Infosys management cautioned regarding discretionary IT spending in North American financial sector.",
        "source": "Business Standard",
        "event_type": "GUIDANCE",
        "sentiment": "NEGATIVE",
        "impact_score": 0.78,
        "published_ago_hours": 6,
    },

    {
        "symbol": "NVDA",
        "title": "NVIDIA faces expanded export restrictions on AI chips to China and Middle East",
        "summary": "US regulators announced expanded restrictions on NVIDIA's H100 and A100 chip exports. The move is expected to impact a significant portion of NVIDIA's data center revenue.",
        "source": "Reuters",
        "event_type": "REGULATORY",
        "sentiment": "NEGATIVE",
        "impact_score": 0.91,
        "published_ago_hours": 3,
    },
    {
        "symbol": "NVDA",
        "title": "Analysts revise NVDA price targets following regulatory news",
        "summary": "Several major banks have lowered their price targets for NVIDIA following the export restriction announcement.",
        "source": "Bloomberg",
        "event_type": "ANALYST",
        "sentiment": "NEGATIVE",
        "impact_score": 0.72,
        "published_ago_hours": 2,
    },
    {
        "symbol": "TSLA",
        "title": "Tesla Q3 earnings exceed analyst expectations, deliveries hit record high",
        "summary": "Tesla reported Q3 EPS of $1.05 vs $0.84 expected. Deliveries reached 515,000 units, beating consensus estimates of 462,000.",
        "source": "CNBC",
        "event_type": "EARNINGS",
        "sentiment": "POSITIVE",
        "impact_score": 0.88,
        "published_ago_hours": 18,
    },
    {
        "symbol": "TSLA",
        "title": "Tesla raises FY guidance following strong Q3 performance",
        "summary": "CEO Elon Musk raised full-year delivery guidance to 2 million vehicles, up from previous guidance of 1.8 million.",
        "source": "WSJ",
        "event_type": "GUIDANCE",
        "sentiment": "POSITIVE",
        "impact_score": 0.80,
        "published_ago_hours": 17,
    },
    {
        "symbol": "AAPL",
        "title": "Apple earnings call scheduled for next week — analysts bullish ahead of iPhone cycle",
        "summary": "Apple is set to report Q4 earnings in 7 days. Analysts are expecting strong iPhone 16 demand figures to drive revenue beat.",
        "source": "MarketWatch",
        "event_type": "EARNINGS",
        "sentiment": "POSITIVE",
        "impact_score": 0.65,
        "published_ago_hours": 6,
    },
]

CHECKPOINT_AGO_HOURS = 20  # "Last checked: 20 hours ago"


def seed():
    print("[*] Seeding PULSE demo data...")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Demo User ──────────────────────────────────────────────────────
        demo_email = "demo@pulse.app"
        user = db.query(User).filter(User.email == demo_email).first()
        if not user:
            user = User(
                email=demo_email,
                password_hash=hash_password("Demo@2026!"),
                name="Alex Demo",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[OK] Demo user created: {demo_email}")
        else:
            print(f"[INFO] Demo user already exists: {demo_email}")

        # ── Stocks ─────────────────────────────────────────────────────────
        stock_map = {}
        for s in DEMO_STOCKS:
            stock = db.query(Stock).filter(Stock.symbol == s["symbol"]).first()
            if not stock:
                stock = Stock(**s)
                db.add(stock)
                db.commit()
                db.refresh(stock)
                print(f"[OK] Stock added: {s['symbol']}")
            stock_map[s["symbol"]] = stock

        # ── Watchlist ──────────────────────────────────────────────────────
        watchlist = db.query(Watchlist).filter(
            Watchlist.user_id == user.id, Watchlist.name == "Tech Portfolio"
        ).first()
        if not watchlist:
            watchlist = Watchlist(user_id=user.id, name="Tech Portfolio")
            db.add(watchlist)
            db.commit()
            db.refresh(watchlist)
            print(f"[OK] Watchlist created: Tech Portfolio")

            for symbol, stock in stock_map.items():
                ws = WatchlistStock(watchlist_id=watchlist.id, stock_id=stock.id)
                db.add(ws)
            db.commit()
            print(f"[OK] Added {len(stock_map)} stocks to watchlist")

        # ── Market Snapshots (checkpoint state) ───────────────────────────
        checkpoint_time = datetime.now(timezone.utc) - timedelta(hours=CHECKPOINT_AGO_HOURS)
        current_time = datetime.now(timezone.utc)

        for symbol, stock in stock_map.items():
            cp_price = CHECKPOINT_PRICES[symbol]
            cur_price = CURRENT_PRICES[symbol]
            cur_vol = CURRENT_VOLUMES[symbol]
            change_pct = ((cur_price - cp_price) / cp_price) * 100

            # Old snapshot (at checkpoint time)
            old_snap = MarketSnapshot(
                stock_id=stock.id,
                price=cp_price,
                previous_close=cp_price * 0.998,
                volume=cur_vol * 0.9,
                change_pct=0.2,
                timestamp=checkpoint_time,
                source="seed",
                data_status="LIVE",
                collected_at=checkpoint_time,
            )
            db.add(old_snap)

            # Current snapshot
            cur_snap = MarketSnapshot(
                stock_id=stock.id,
                price=cur_price,
                previous_close=cp_price,
                volume=float(cur_vol),
                change_pct=change_pct,
                timestamp=current_time,
                source="seed",
                data_status="LIVE",
                collected_at=current_time,
            )
            db.add(cur_snap)

        db.commit()
        print(f"[OK] Market snapshots seeded")

        # ── Checkpoints (user's last-seen state) ──────────────────────────
        for symbol, stock in stock_map.items():
            existing = db.query(Checkpoint).filter(
                Checkpoint.user_id == user.id,
                Checkpoint.watchlist_id == watchlist.id,
                Checkpoint.stock_id == stock.id,
            ).first()
            if not existing:
                cp = Checkpoint(
                    user_id=user.id,
                    watchlist_id=watchlist.id,
                    stock_id=stock.id,
                    price=CHECKPOINT_PRICES[symbol],
                    volume=CURRENT_VOLUMES[symbol] * 0.9,
                    attention_score=20.0,
                    created_at=checkpoint_time,
                )
                db.add(cp)
        db.commit()
        print(f"[OK] Checkpoints seeded (last checked: {CHECKPOINT_AGO_HOURS}h ago)")

        # ── News ───────────────────────────────────────────────────────────
        import hashlib
        for article in DEMO_NEWS:
            sym = article.pop("symbol")
            hours_ago = article.pop("published_ago_hours")
            stock = stock_map.get(sym)
            if not stock:
                continue

            url = f"https://demo-pulse.app/news/{sym.lower()}-{hours_ago}"
            url_hash = hashlib.md5(url.encode()).hexdigest()

            if not db.query(News).filter(News.url_hash == url_hash).first():
                news = News(
                    stock_id=stock.id,
                    title=article["title"],
                    summary=article["summary"],
                    source=article["source"],
                    url=url,
                    url_hash=url_hash,
                    published_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
                    sentiment=article["sentiment"],
                    impact_score=article["impact_score"],
                    event_type=article["event_type"],
                )
                db.add(news)
        db.commit()
        print(f"[OK] Demo news seeded")

        print("\n" + "="*60)
        print("PULSE Demo Data Ready!")
        print("="*60)
        print(f"  Email:    demo@pulse.app")
        print(f"  Password: Demo@2026!")
        print(f"  Watchlist: Tech Portfolio ({len(stock_map)} stocks)")
        print(f"  Last checked: {CHECKPOINT_AGO_HOURS} hours ago")
        print()
        print("  Demo scenario:")
        print("    [MAJOR]     NVDA  -5.2%  Attention 92")
        print("    [MAJOR]     TSLA  +6.1%  Attention 81")
        print("    [IMPORTANT] AAPL  +0.1%  Attention 67  (earnings)")
        print("    [NORMAL]    Others  Normal — no action needed")
        print("="*60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()



if __name__ == "__main__":
    seed()
