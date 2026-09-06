"""
Market hours detection utility.
Determines whether a given exchange/symbol is currently in live trading hours.
"""
from datetime import datetime, timezone
from typing import Literal

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False


MarketStatus = Literal["LIVE", "PRE_MARKET", "AFTER_HOURS", "MARKET_CLOSED"]


def get_market_status(symbol: str = "") -> MarketStatus:
    """
    Returns the current trading status for a given symbol.
    - Indian symbols (.NS / .BO): NSE/BSE hours IST Mon-Fri 09:15-15:30
    - US symbols: NYSE/NASDAQ hours ET Mon-Fri 09:30-16:00
    """
    is_indian = symbol.upper().endswith(".NS") or symbol.upper().endswith(".BO")

    if not PYTZ_AVAILABLE:
        # Without pytz, default to closed (safe fallback)
        return "MARKET_CLOSED"

    now_utc = datetime.now(timezone.utc)

    if is_indian:
        import pytz
        ist = pytz.timezone("Asia/Kolkata")
        now_local = now_utc.astimezone(ist)
        # NSE/BSE: Mon-Fri only
        if now_local.weekday() >= 5:
            return "MARKET_CLOSED"
        market_open = now_local.replace(hour=9, minute=15, second=0, microsecond=0)
        pre_open   = now_local.replace(hour=9, minute=0,  second=0, microsecond=0)
        market_close = now_local.replace(hour=15, minute=30, second=0, microsecond=0)

        if now_local < pre_open:
            return "MARKET_CLOSED"
        elif now_local < market_open:
            return "PRE_MARKET"
        elif now_local <= market_close:
            return "LIVE"
        else:
            return "AFTER_HOURS"
    else:
        # US markets
        import pytz
        et = pytz.timezone("America/New_York")
        now_local = now_utc.astimezone(et)
        if now_local.weekday() >= 5:
            return "MARKET_CLOSED"
        pre_open     = now_local.replace(hour=4,  minute=0,  second=0, microsecond=0)
        market_open  = now_local.replace(hour=9,  minute=30, second=0, microsecond=0)
        market_close = now_local.replace(hour=16, minute=0,  second=0, microsecond=0)
        after_close  = now_local.replace(hour=20, minute=0,  second=0, microsecond=0)

        if now_local < pre_open:
            return "MARKET_CLOSED"
        elif now_local < market_open:
            return "PRE_MARKET"
        elif now_local <= market_close:
            return "LIVE"
        elif now_local <= after_close:
            return "AFTER_HOURS"
        else:
            return "MARKET_CLOSED"


def is_market_live(symbol: str = "") -> bool:
    """Returns True only during regular trading hours."""
    return get_market_status(symbol) == "LIVE"
