"""
Gemini AI explanation service.
Sends structured evidence payload to Gemini and parses explanation.
Falls back to algorithmic explanation if no API key.
"""
import json
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


EXPLANATION_PROMPT_TEMPLATE = """You are a financial analyst assistant. Analyze the following market data and provide a structured explanation.

STOCK DATA:
{evidence}

INSTRUCTIONS:
- Explain what changed and why it is unusual
- Identify likely contributing factors (do NOT claim causality — use "appears to be", "may be related to", "evidence suggests")
- Do NOT provide investment advice
- Do NOT invent facts not present in the data
- Be concise and factual

Respond in this exact JSON format:
{{
  "summary": "One sentence summary of what happened and why it's notable",
  "drivers": [
    {{"factor": "Factor name", "weight": 0.45, "description": "Brief explanation"}},
    {{"factor": "Factor name", "weight": 0.27, "description": "Brief explanation"}}
  ],
  "confidence": 82,
  "caveat": "One sentence about limitations of this analysis"
}}"""


RANGE_EXPLANATION_PROMPT_TEMPLATE = """You are a senior equity research analyst. Analyze the stock movement and news events between {start_date} and {end_date}.

STOCK & MARKET RANGE DATA:
{evidence}

INSTRUCTIONS:
- Explain what primary news events, earnings releases, corporate developments, or macroeconomic factors caused the price change over this specific date range ({start_date} to {end_date}).
- Use evidence from the provided news items and price/volume metrics.
- Do NOT claim absolute causality — use phraseology like "driven primarily by", "may be attributed to", "coincided with".
- Do NOT provide investment advice.
- Be clear, professional, and concise.

Respond in this exact JSON format:
{{
  "summary": "Detailed 2-3 sentence executive summary explaining what caused the price movement between {start_date} and {end_date} based on news and market events.",
  "drivers": [
    {{"factor": "Factor name (e.g. Q3 Earnings / Product Release / Sector Rally)", "weight": 0.50, "description": "Brief explanation connecting news to price move"}},
    {{"factor": "Factor name", "weight": 0.30, "description": "Brief explanation"}}
  ],
  "key_events": [
    {{"date": "YYYY-MM-DD", "event": "Event title/description", "impact": "POSITIVE/NEGATIVE/NEUTRAL"}}
  ],
  "confidence": 85,
  "caveat": "One sentence acknowledging attribution limitations and date range boundary."
}}"""


class GeminiExplainer:

    def __init__(self):
        self._client = None
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                for model_name in ["gemini-3.6-flash", "gemini-1.5-pro", "gemini-flash-latest", "gemini-pro-latest", "gemini-2.0-flash"]:
                    try:
                        self._client = genai.GenerativeModel(model_name)
                        logger.info(f"Gemini AI client initialized with {model_name}")
                        break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

    def explain(self, evidence: dict) -> dict:
        """Generate AI explanation from structured evidence."""
        if not self._client:
            return self._algorithmic_explanation(evidence)

        try:
            prompt = EXPLANATION_PROMPT_TEMPLATE.format(
                evidence=json.dumps(evidence, indent=2)
            )
            response = self._client.generate_content(prompt)
            text = response.text.strip()

            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            return result

        except Exception as e:
            logger.error(f"Gemini explanation error: {e}")
            return self._algorithmic_explanation(evidence)

    def explain_range(self, evidence: dict) -> dict:
        """Generate AI explanation for stock movement across a specific date range."""
        start_date = evidence.get("start_date", "Start Date")
        end_date = evidence.get("end_date", "End Date")

        if not self._client:
            return self._algorithmic_range_explanation(evidence)

        try:
            prompt = RANGE_EXPLANATION_PROMPT_TEMPLATE.format(
                start_date=start_date,
                end_date=end_date,
                evidence=json.dumps(evidence, indent=2),
            )
            response = self._client.generate_content(prompt)
            text = response.text.strip()

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            return result
        except Exception as e:
            logger.error(f"Gemini range explanation error: {e}")
            return self._algorithmic_range_explanation(evidence)

    def _algorithmic_explanation(self, evidence: dict) -> dict:
        """
        Fallback: generate explanation from evidence without AI.
        Used when no Gemini API key or API fails.
        """
        symbol = evidence.get("symbol", "This stock")
        price_change = evidence.get("price_change_pct", 0)
        z_score = evidence.get("z_score", 0)
        volume_ratio = evidence.get("volume_ratio", 1)
        market_change = evidence.get("market_return_pct", 0)
        sector_change = evidence.get("sector_return_pct", 0)
        company_pct = evidence.get("company_specific_pct", 50)
        sector_pct = evidence.get("sector_pct", 25)
        market_pct = evidence.get("market_pct", 25)
        news = evidence.get("news", [])

        direction = "fell" if price_change < 0 else "rose"
        magnitude = abs(price_change)

        # Severity language
        if abs(z_score) > 3:
            unusualness = "significantly more than its historical norm"
        elif abs(z_score) > 2:
            unusualness = "more than its typical daily movement"
        else:
            unusualness = "outside its normal range"

        summary = (
            f"{symbol} {direction} {magnitude:.1f}%, "
            f"{unusualness}. "
            f"{'Heavy trading volume (' + str(round(volume_ratio, 1)) + 'x average) accompanied the move. ' if volume_ratio > 1.5 else ''}"
            f"{'News activity was detected during this period.' if news else ''}"
        )

        drivers = []
        if company_pct > 10:
            drivers.append({
                "factor": "Company-specific signals",
                "weight": round(company_pct / 100, 2),
                "description": f"Idiosyncratic movement not explained by market or sector ({company_pct:.0f}% of move)",
            })
        if sector_pct > 5:
            drivers.append({
                "factor": "Sector movement",
                "weight": round(sector_pct / 100, 2),
                "description": f"Sector-wide trend contributed {sector_pct:.0f}% of the move (sector change: {sector_change:.1f}%)",
            })
        if market_pct > 5:
            drivers.append({
                "factor": "Broad market movement",
                "weight": round(market_pct / 100, 2),
                "description": f"General market direction (SPY: {market_change:.1f}%) contributed {market_pct:.0f}%",
            })
        if news:
            drivers.append({
                "factor": "News activity",
                "weight": 0.15,
                "description": f"{len(news)} relevant article(s) published during this period",
            })

        return {
            "summary": summary.strip(),
            "drivers": drivers[:4],
            "confidence": max(40, min(90, int(50 + abs(z_score) * 10))),
            "caveat": "Attribution is evidence-based estimation, not proof of causation. This is not investment advice.",
        }

    def _algorithmic_range_explanation(self, evidence: dict) -> dict:
        """Fallback range explanation generator when Gemini API is unavailable."""
        symbol = evidence.get("symbol", "Stock")
        start_date = evidence.get("start_date", "start date")
        end_date = evidence.get("end_date", "end date")
        price_change_pct = evidence.get("price_change_pct", 0.0)
        start_price = evidence.get("start_price", 0.0)
        end_price = evidence.get("end_price", 0.0)
        news = evidence.get("news", [])
        currency = evidence.get("currency", "₹" if symbol.endswith((".NS", ".BO")) else "$")

        direction = "gained" if price_change_pct >= 0 else "declined"
        summary = (
            f"Between {start_date} and {end_date}, {symbol} {direction} {abs(price_change_pct):.2f}% "
            f"from {currency}{start_price:.2f} to {currency}{end_price:.2f}. "
            f"{f'During this timeframe, {len(news)} key news articles were published regarding {symbol}.' if news else 'Limited news coverage was logged during this timeframe.'}"
        )

        drivers = []
        if news:
            drivers.append({
                "factor": "News & Market Announcements",
                "weight": 0.45,
                "description": f"{len(news)} news development(s) occurred during the selected period."
            })
            drivers.append({
                "factor": "Company Dynamics",
                "weight": 0.35,
                "description": f"Internal company performance and trading volume trends."
            })
            drivers.append({
                "factor": "Macro & Sector Environment",
                "weight": 0.20,
                "description": "Broader index trends and sector market sentiment."
            })
        else:
            drivers.append({
                "factor": "Technical & Trend Dynamics",
                "weight": 0.60,
                "description": f"Price trend continuation between {start_date} and {end_date}."
            })
            drivers.append({
                "factor": "Macro & Index Correlation",
                "weight": 0.40,
                "description": "Overall equity market movement during this timeframe."
            })

        key_events = []
        for item in news[:5]:
            pub = item.get("published_at", start_date)
            if pub and "T" in pub:
                pub = pub.split("T")[0]
            key_events.append({
                "date": pub,
                "event": item.get("title", "Market Update"),
                "impact": "POSITIVE" if price_change_pct >= 0 else "NEGATIVE",
            })

        return {
            "summary": summary,
            "drivers": drivers,
            "key_events": key_events,
            "confidence": 75 if news else 60,
            "caveat": f"Analysis covers news and prices between {start_date} and {end_date}. Past performance is not financial advice.",
        }


gemini_explainer = GeminiExplainer()
