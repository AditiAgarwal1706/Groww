"""
yfinance 1.7.0 market data provider.
No API key required. Returns real market data.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

# Sector ETF mapping for attribution analysis
SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Financial Services": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Cyclical": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Communication Services": "XLC",
}


class YFinanceProvider:
    """Primary market data provider using yfinance (free, no API key)."""

    def get_quote(self, symbol: str) -> Optional[dict]:
        """Fetch current quote for a symbol using history (most reliable in yfinance 1.7)."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1d")

            if hist.empty:
                logger.warning(f"No history data for {symbol}")
                return None

            latest = hist.iloc[-1]
            prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else latest.get("Open")
            price = float(latest["Close"])
            if pd.isna(price) or price <= 0:
                return None

            change_pct = None
            if prev_close is not None and not pd.isna(prev_close) and float(prev_close) > 0:
                change_pct = float(((price - float(prev_close)) / float(prev_close)) * 100)

            # Get market cap from info (best-effort, may be slow)
            market_cap = None
            try:
                info = ticker.info
                market_cap = info.get("marketCap") or info.get("market_cap")
            except Exception:
                pass

            return {
                "symbol": symbol,
                "price": price,
                "open": float(latest["Open"]) if "Open" in latest.index and not pd.isna(latest["Open"]) else None,
                "high": float(latest["High"]) if "High" in latest.index and not pd.isna(latest["High"]) else None,
                "low": float(latest["Low"]) if "Low" in latest.index and not pd.isna(latest["Low"]) else None,
                "previous_close": float(prev_close) if prev_close is not None and not pd.isna(prev_close) else None,
                "volume": float(latest["Volume"]) if "Volume" in latest.index and not pd.isna(latest["Volume"]) else None,
                "change_pct": change_pct,
                "market_cap": market_cap,
                "timestamp": datetime.now(timezone.utc),
                "source": "yfinance",
                "data_status": "LIVE",
            }
        except Exception as e:
            logger.error(f"yfinance quote error for {symbol}: {e}")
            return None

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, dict]:
        """
        Fetch current quotes for multiple symbols in a single batch call.
        yfinance 1.7.0 MultiIndex format: data['Close']['SYMBOL']
        """
        if not symbols:
            return {}

        symbols = list(set([s.upper() for s in symbols]))
        results = {}
        now = datetime.now(timezone.utc)

        try:
            if len(symbols) == 1:
                # Single symbol — use individual Ticker.history for reliability
                q = self.get_quote(symbols[0])
                if q:
                    results[symbols[0]] = q
                return results

            # Multi-symbol batch download
            data = yf.download(
                symbols,
                period="5d",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )

            if data.empty:
                raise ValueError("Empty batch response")

            # yfinance 1.7.0: MultiIndex is (field, symbol) — e.g. data['Close']['AAPL']
            close_data = data["Close"] if "Close" in data.columns.get_level_values(0) else None
            open_data = data["Open"] if "Open" in data.columns.get_level_values(0) else None
            high_data = data["High"] if "High" in data.columns.get_level_values(0) else None
            low_data = data["Low"] if "Low" in data.columns.get_level_values(0) else None
            vol_data = data["Volume"] if "Volume" in data.columns.get_level_values(0) else None

            if close_data is None or close_data.empty:
                raise ValueError("No Close data in batch response")

            for symbol in symbols:
                try:
                    if symbol not in close_data.columns:
                        continue

                    closes = close_data[symbol].dropna()
                    if closes.empty or len(closes) < 1:
                        continue

                    price = float(closes.iloc[-1])
                    if pd.isna(price) or price <= 0:
                        continue

                    prev_close = float(closes.iloc[-2]) if len(closes) > 1 else None
                    change_pct = 0.0
                    if prev_close and not pd.isna(prev_close) and prev_close > 0:
                        change_pct = float(((price - prev_close) / prev_close) * 100)

                    def _safe_last(series_data, sym):
                        try:
                            if series_data is None or sym not in series_data.columns:
                                return None
                            s = series_data[sym].dropna()
                            return float(s.iloc[-1]) if not s.empty else None
                        except Exception:
                            return None

                    results[symbol] = {
                        "symbol": symbol,
                        "price": price,
                        "open": _safe_last(open_data, symbol),
                        "high": _safe_last(high_data, symbol),
                        "low": _safe_last(low_data, symbol),
                        "previous_close": prev_close,
                        "volume": _safe_last(vol_data, symbol),
                        "change_pct": change_pct,
                        "market_cap": None,
                        "timestamp": now,
                        "source": "yfinance",
                        "data_status": "LIVE",
                    }
                except Exception as ex:
                    logger.debug(f"Batch item extraction error for {symbol}: {ex}")

        except Exception as e:
            logger.error(f"Batch quotes download error: {e}")

        # Fallback: fetch individually for any symbols missed by batch download
        missed = [s for s in symbols if s not in results]
        if missed:
            logger.info(f"Falling back to individual fetch for: {missed}")
            for symbol in missed:
                q = self.get_quote(symbol)
                if q:
                    results[symbol] = q

        return results

    def get_history(self, symbol: str, days: int = 30) -> List[dict]:
        """Fetch OHLCV history."""
        try:
            ticker = yf.Ticker(symbol)
            period = f"{days}d"
            hist = ticker.history(period=period, interval="1d")
            if hist.empty:
                return []
            result = []
            for date, row in hist.iterrows():
                result.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                })
            return result
        except Exception as e:
            logger.error(f"yfinance history error for {symbol}: {e}")
            return []

    def get_company_info(self, symbol: str) -> dict:
        """Get company metadata for stock seeding or dynamic search."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            sector = info.get("sector", None)
            company_name = info.get("longName") or info.get("shortName") or symbol
            # Validate it's a real ticker (not empty/error)
            if not company_name or company_name == symbol:
                # Try fast_info as fallback
                try:
                    fi = ticker.fast_info
                    if hasattr(fi, "currency") and fi.currency:
                        company_name = symbol
                except Exception:
                    pass
            is_indian = symbol.endswith(".NS") or symbol.endswith(".BO") or info.get("currency") == "INR" or info.get("exchange") in ["NSI", "BSE", "NSE"]
            currency = "INR" if is_indian else info.get("currency", "USD")
            default_benchmark = "^NSEI" if is_indian else "SPY"
            exchange = "NSE" if symbol.endswith(".NS") else ("BSE" if symbol.endswith(".BO") else info.get("exchange", "NASDAQ"))

            return {
                "company_name": company_name,
                "exchange": exchange,
                "sector": sector,
                "sector_etf": SECTOR_ETF_MAP.get(sector, default_benchmark),
                "currency": currency,
            }
        except Exception as e:
            logger.error(f"yfinance info error for {symbol}: {e}")
            is_indian = symbol.endswith(".NS") or symbol.endswith(".BO")
            return {
                "company_name": symbol,
                "exchange": "NSE" if symbol.endswith(".NS") else ("BSE" if symbol.endswith(".BO") else "US"),
                "sector": "General",
                "sector_etf": "^NSEI" if is_indian else "SPY",
                "currency": "INR" if is_indian else "USD",
            }



yfinance_provider = YFinanceProvider()
