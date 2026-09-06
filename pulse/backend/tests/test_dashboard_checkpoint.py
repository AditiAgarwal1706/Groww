"""
Tests for Dashboard and Checkpoint API endpoints.
"""

def test_get_dashboard(client, auth_headers, test_watchlist):
    response = client.get("/api/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["watchlist_id"] == test_watchlist.id
    assert "summary" in data
    assert "top_attention" in data
    assert "watchlist" in data




def test_save_checkpoint(client, auth_headers, test_watchlist):
    response = client.post(
        f"/api/watchlists/{test_watchlist.id}/checkpoint",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_get_stock_analysis(client, auth_headers, test_stock):
    response = client.get(f"/api/stocks/{test_stock.symbol}/analysis", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "attention_score" in data
    assert "attribution" in data


def test_get_stock_explanation(client, auth_headers, test_stock):
    response = client.get(f"/api/stocks/{test_stock.symbol}/explanation", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "confidence" in data
    assert "drivers" in data


def test_get_stock_timeline(client, auth_headers, test_stock):
    response = client.get(f"/api/stocks/{test_stock.symbol}/timeline", headers=auth_headers)
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)



