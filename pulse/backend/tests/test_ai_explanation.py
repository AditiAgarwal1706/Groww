"""
Tests for Gemini AI Explanation service and algorithmic fallback logic.
"""
from unittest.mock import MagicMock
from app.services.ai.explanation import GeminiExplainer


def test_algorithmic_explanation_fallback():
    explainer = GeminiExplainer()
    evidence = {
        "symbol": "RELIANCE.NS",
        "price_change_pct": 3.45,
        "z_score": 2.8,
        "volume_ratio": 2.1,
        "market_return_pct": 0.5,
        "sector_return_pct": 1.2,
        "company_specific_pct": 60.0,
        "sector_pct": 25.0,
        "market_pct": 15.0,
        "news": [
            {"title": "Reliance Q2 Results Beat Estimates", "impact_score": 0.85}
        ]
    }
    
    result = explainer._algorithmic_explanation(evidence)
    
    assert "summary" in result
    assert "drivers" in result
    assert "confidence" in result
    assert "caveat" in result
    
    assert "RELIANCE.NS" in result["summary"]
    assert "rose 3.5%" in result["summary"] or "rose" in result["summary"]
    assert len(result["drivers"]) > 0
    assert result["confidence"] >= 40 and result["confidence"] <= 90
    assert "investment advice" in result["caveat"]


def test_explanation_driver_weights():
    explainer = GeminiExplainer()
    evidence = {
        "symbol": "TCS.NS",
        "price_change_pct": -4.2,
        "z_score": -3.5,
        "volume_ratio": 3.0,
        "company_specific_pct": 70.0,
        "sector_pct": 20.0,
        "market_pct": 10.0,
    }
    
    result = explainer.explain(evidence)  # Calls fallback if no key
    
    for driver in result["drivers"]:
        assert "factor" in driver
        assert "weight" in driver
        assert "description" in driver
        assert 0.0 <= driver["weight"] <= 1.0


def test_gemini_parsing_mocked():
    explainer = GeminiExplainer()
    mock_client = MagicMock()
    
    json_response = '''
    ```json
    {
      "summary": "TCS.NS experienced a 4.2% decline due to sector weakness and high volume.",
      "drivers": [
        {"factor": "Sector selloff", "weight": 0.60, "description": "IT index dropped 3%"},
        {"factor": "Earnings miss", "weight": 0.40, "description": "Operating margins shrank"}
      ],
      "confidence": 88,
      "caveat": "Based on available 24h market news and technical indicators."
    }
    ```
    '''
    mock_client.generate_content.return_value = MagicMock(text=json_response)
    explainer._client = mock_client
    
    result = explainer.explain({"symbol": "TCS.NS"})
    
    assert result["summary"] == "TCS.NS experienced a 4.2% decline due to sector weakness and high volume."
    assert len(result["drivers"]) == 2
    assert result["confidence"] == 88
    assert result["caveat"] == "Based on available 24h market news and technical indicators."
