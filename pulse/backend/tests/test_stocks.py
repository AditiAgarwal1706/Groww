"""
Tests for stock search and detail endpoints.
"""

def test_search_stocks(client, auth_headers, test_stock):
    response = client.get("/api/stocks/search?q=NVD", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert any(s["symbol"] == "NVDA" for s in results)


def test_get_stock_quote(client, auth_headers, test_stock):
    response = client.get(f"/api/stocks/{test_stock.symbol}/quote", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "price" in data


def test_get_stock_history(client, auth_headers, test_stock):
    response = client.get(f"/api/stocks/{test_stock.symbol}/history?days=14", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "history" in data

