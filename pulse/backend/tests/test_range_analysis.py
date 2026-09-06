import pytest
from datetime import datetime, timedelta
from app.services.ai.explanation import gemini_explainer


def test_explain_range_fallback():
    """Test algorithmic fallback for range explanation when Gemini client is offline."""
    evidence = {
        "symbol": "RELIANCE.NS",
        "company_name": "Reliance Industries Ltd",
        "currency": "₹",
        "start_date": "2026-08-01",
        "end_date": "2026-08-15",
        "start_price": 2500.0,
        "end_price": 2720.0,
        "price_change": 220.0,
        "price_change_pct": 8.8,
        "news": [
            {
                "title": "Reliance Q1 profit jumps 15% on retail strength",
                "published_at": "2026-08-05T10:00:00Z",
                "event_type": "EARNINGS",
            }
        ],
    }

    result = gemini_explainer.explain_range(evidence)

    assert "summary" in result
    assert "drivers" in result
    assert "key_events" in result
    assert "confidence" in result
    assert "caveat" in result
    assert "RELIANCE.NS" in result["summary"]
    assert len(result["drivers"]) > 0


def test_range_analysis_api_validation(client, auth_headers):
    """Test invalid date range parameters produce 400 error."""
    # start_date > end_date
    res = client.get(
        "/api/stocks/RELIANCE.NS/range-analysis?start_date=2026-08-15&end_date=2026-08-01",
        headers=auth_headers
    )
    assert res.status_code == 400
    assert "start_date must be before or equal to end_date" in res.json()["detail"]

    # Invalid date format
    res_bad_format = client.get(
        "/api/stocks/RELIANCE.NS/range-analysis?start_date=01-08-2026&end_date=15-08-2026",
        headers=auth_headers
    )
    assert res_bad_format.status_code == 400


def test_range_analysis_api_success(client, auth_headers, db_session):
    """Test successful range analysis endpoint response."""
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    res = client.get(
        f"/api/stocks/RELIANCE.NS/range-analysis?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()

    assert data["symbol"] == "RELIANCE.NS"
    assert data["start_date"] == start_date
    assert data["end_date"] == end_date
    assert "start_price" in data
    assert "end_price" in data
    assert "price_change_pct" in data
    assert "ai_explanation" in data
    assert "summary" in data["ai_explanation"]
