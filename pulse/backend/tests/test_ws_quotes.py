"""
Tests for WebSocket quote streaming endpoint.
"""
import pytest
from starlette.websockets import WebSocketDisconnect
from app.core.security import create_access_token


def test_ws_quotes_unauthorized(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/quotes?token=invalidtoken"):
            pass



def test_ws_quotes_authorized(client, test_user, test_watchlist):
    token = create_access_token(str(test_user.id))
    url = f"/ws/quotes?token={token}&watchlist_id={test_watchlist.id}"

    with client.websocket_connect(url) as websocket:
        # Receive first quotes frame
        data = websocket.receive_json()
        assert data["type"] in ["quotes", "heartbeat"]
        if data["type"] == "quotes":
            assert "data" in data
            assert "NVDA" in data["data"]
            assert "price" in data["data"]["NVDA"]

        # Send ping message
        websocket.send_json({"action": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"

