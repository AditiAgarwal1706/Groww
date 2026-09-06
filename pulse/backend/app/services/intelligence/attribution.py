"""
Movement Attribution Engine.
Decomposes a stock's movement into:
  - Market effect (broad market beta)
  - Sector effect (sector drift)
  - Company-specific (idiosyncratic)
"""
import yfinance as yf
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Attribution:
    stock_return: float         # total observed return (decimal)
    market_return: float        # SPY return for same period
    sector_return: float        # Sector ETF return for same period
    market_effect: float        # portion explained by market
    sector_effect: float        # portion explained by sector (net of market)
    company_specific: float     # idiosyncratic (residual)
    market_pct: float           # percentage of move
    sector_pct: float
    company_pct: float


def _fetch_etf_return(symbol: str, days: int = 1) -> float:
    """Fetch return for an ETF over the last N trading days."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{max(days+5, 7)}d", interval="1d")
        if len(hist) < 2:
            return 0.0
        closes = hist["Close"].values
        # Return over the period
        ret = (closes[-1] - closes[-max(days, 1)]) / closes[-max(days, 1)]
        return float(ret)
    except Exception as e:
        logger.warning(f"Could not fetch ETF return for {symbol}: {e}")
        return 0.0


def compute_attribution(
    stock_return: float,         # decimal (e.g. -0.052 for -5.2%)
    sector_etf: str = "SPY",    # sector ETF symbol
    period_days: int = 1,        # period over which return was computed
) -> Attribution:
    """
    Decompose stock return into market, sector, company components.

    Method (simplified linear attribution):
      market_effect   = SPY return (broad market)
      sector_effect   = Sector ETF return - SPY return (sector drift net of market)
      company_specific = stock_return - sector_etf_return (residual)
    """
    market_ret = _fetch_etf_return("SPY", period_days)
    sector_ret = _fetch_etf_return(sector_etf, period_days) if sector_etf != "SPY" else market_ret

    market_effect = market_ret
    sector_effect = sector_ret - market_ret
    company_specific = stock_return - sector_ret

    # Compute percentage contributions (absolute weights)
    total_abs = abs(market_effect) + abs(sector_effect) + abs(company_specific)
    if total_abs == 0:
        market_pct = sector_pct = company_pct = 0.0
    else:
        market_pct = (abs(market_effect) / total_abs) * 100
        sector_pct = (abs(sector_effect) / total_abs) * 100
        company_pct = (abs(company_specific) / total_abs) * 100

    return Attribution(
        stock_return=stock_return,
        market_return=market_ret,
        sector_return=sector_ret,
        market_effect=market_effect,
        sector_effect=sector_effect,
        company_specific=company_specific,
        market_pct=round(market_pct, 1),
        sector_pct=round(sector_pct, 1),
        company_pct=round(company_pct, 1),
    )
