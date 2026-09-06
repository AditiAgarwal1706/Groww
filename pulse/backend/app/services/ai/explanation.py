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


class GeminiExplainer:

    def __init__(self):
        self._client = None
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._client = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Gemini AI client initialized")
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


gemini_explainer = GeminiExplainer()
