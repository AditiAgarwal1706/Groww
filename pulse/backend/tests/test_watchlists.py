"""
Tests for Watchlist API endpoints.
"""

def test_list_watchlists_empty(client, auth_headers):
    response = client.get("/api/watchlists/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_watchlist(client, auth_headers):
    response = client.post(
        "/api/watchlists/",
        json={"name": "Growth Stocks"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Growth Stocks"
    assert "id" in data



def test_get_watchlist_detail(client, auth_headers, test_watchlist):
    response = client.get(f"/api/watchlists/{test_watchlist.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_watchlist.id
    assert data["name"] == test_watchlist.name
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["stock"]["symbol"] == "NVDA"


def test_add_stock_to_watchlist(client, auth_headers, test_watchlist):
    response = client.post(
        f"/api/watchlists/{test_watchlist.id}/stocks",
        json={"symbol": "AAPL"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "message" in data

    # Verify stock count increased
    detail_res = client.get(f"/api/watchlists/{test_watchlist.id}", headers=auth_headers)
    assert len(detail_res.json()["stocks"]) == 2


def test_remove_stock_from_watchlist(client, auth_headers, test_watchlist):
    response = client.delete(
        f"/api/watchlists/{test_watchlist.id}/stocks/NVDA",
        headers=auth_headers,
    )
    assert response.status_code == 204

    detail_res = client.get(f"/api/watchlists/{test_watchlist.id}", headers=auth_headers)
    assert len(detail_res.json()["stocks"]) == 0



def test_delete_watchlist(client, auth_headers, test_watchlist):
    response = client.delete(f"/api/watchlists/{test_watchlist.id}", headers=auth_headers)
    assert response.status_code == 204

    get_res = client.get(f"/api/watchlists/{test_watchlist.id}", headers=auth_headers)
    assert get_res.status_code == 404

