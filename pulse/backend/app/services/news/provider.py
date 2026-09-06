"""
NewsAPI.org provider for real market news.
Falls back to mock data if no API key configured.
"""
import httpx
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

NEWS_API_BASE = "https://newsapi.org/v2/everything"

# Event type keyword mapping
EVENT_KEYWORDS = {
    "EARNINGS": ["earnings", "profit", "revenue", "eps", "quarterly results", "beat", "miss", "guidance"],
    "REGULATORY": ["sec", "ftc", "antitrust", "investigation", "fine", "penalty", "compliance", "regulation"],
    "ACQUISITION": ["acquire", "merger", "takeover", "buyout", "deal", "acquisition"],
    "PRODUCT": ["launch", "product", "release", "unveil", "announced", "new model"],
    "MANAGEMENT": ["ceo", "cfo", "resign", "appoint", "executive", "leadership"],
    "ANALYST": ["upgrade", "downgrade", "price target", "analyst", "rating"],
    "LEGAL": ["lawsuit", "settlement", "court", "sued", "litigation"],
    "PARTNERSHIP": ["partnership", "collaboration", "contract", "agreement"],
    "MACRO": ["fed", "interest rate", "inflation", "gdp", "recession", "tariff"],
}

SENTIMENT_POSITIVE = ["surge", "soar", "beat", "record", "growth", "profit", "gain", "rise", "jump", "rally"]
SENTIMENT_NEGATIVE = ["fall", "drop", "miss", "loss", "decline", "plunge", "crash", "investigation", "fine", "cut"]


def _classify_event_type(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return event_type
    return "OTHER"


def _classify_sentiment(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    pos = sum(1 for w in SENTIMENT_POSITIVE if w in text)
    neg = sum(1 for w in SENTIMENT_NEGATIVE if w in text)
    if pos > neg:
        return "POSITIVE"
    elif neg > pos:
        return "NEGATIVE"
    return "NEUTRAL"


def _score_impact(title: str, event_type: str, sentiment: str) -> float:
    """Rough impact scoring based on event type and sentiment."""
    base_scores = {
        "EARNINGS": 0.75,
        "REGULATORY": 0.85,
        "ACQUISITION": 0.80,
        "MANAGEMENT": 0.70,
        "LEGAL": 0.80,
        "ANALYST": 0.55,
        "PRODUCT": 0.60,
        "PARTNERSHIP": 0.50,
        "MACRO": 0.65,
        "OTHER": 0.40,
    }
    score = base_scores.get(event_type, 0.40)
    # Strong sentiment words boost impact
    if sentiment != "NEUTRAL":
        score = min(1.0, score + 0.1)
    return round(score, 2)


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


class NewsProvider:

    def fetch_news(self, symbol: str, company_name: str, days_back: int = 3) -> List[dict]:
        """Fetch news from NewsAPI.org. Falls back to mock if no key."""
        if not settings.NEWS_API_KEY:
            logger.info(f"No NEWS_API_KEY — returning mock news for {symbol}")
            return self._mock_news(symbol)

        from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        query = f"{symbol} OR {company_name.split()[0]}"

        try:
            resp = httpx.get(
                NEWS_API_BASE,
                params={
                    "q": query,
                    "from": from_date,
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 10,
                    "apiKey": settings.NEWS_API_KEY,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])

            result = []
            for art in articles:
                title = art.get("title", "")
                summary = art.get("description", "") or ""
                url = art.get("url", "")
                if not title or not url:
                    continue

                event_type = _classify_event_type(title, summary)
                sentiment = _classify_sentiment(title, summary)
                impact = _score_impact(title, event_type, sentiment)

                published_raw = art.get("publishedAt", "")
                try:
                    published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                except Exception:
                    published_at = datetime.now(timezone.utc)

                result.append({
                    "title": title,
                    "summary": summary[:500] if summary else None,
                    "source": art.get("source", {}).get("name"),
                    "url": url,
                    "url_hash": _url_hash(url),
                    "published_at": published_at,
                    "sentiment": sentiment,
                    "impact_score": impact,
                    "event_type": event_type,
                })
            return result

        except Exception as e:
            logger.error(f"NewsAPI error for {symbol}: {e}")
            return self._mock_news(symbol)

    def _mock_news(self, symbol: str) -> List[dict]:
        """Demo-safe fallback news."""
        return [
            {
                "title": f"Analysts update outlook on {symbol} amid market uncertainty",
                "summary": f"Multiple analysts revised their price targets for {symbol} following recent sector trends.",
                "source": "Market Watch",
                "url": f"https://example.com/news/{symbol.lower()}-1",
                "url_hash": _url_hash(f"mock-{symbol}-1"),
                "published_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "sentiment": "NEUTRAL",
                "impact_score": 0.45,
                "event_type": "ANALYST",
            }
        ]


news_provider = NewsProvider()
