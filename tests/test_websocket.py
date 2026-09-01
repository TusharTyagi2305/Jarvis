import pytest
from fastapi.testclient import TestClient
from jarvis.api.app import app

client = TestClient(app)

def test_websocket_connection_and_events():
    with client.websocket_connect("/ws") as websocket:
        # Verify initial state event
        data = websocket.receive_json()
        assert data["type"] == "state"
        assert data["state"] == "IDLE"

        # Send ping
        websocket.send_text("ping")
        pong = websocket.receive_json()
        assert pong["type"] == "pong"

def test_command_endpoint_and_broadcasting():
    with client.websocket_connect("/ws") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "state"

        # Post command via REST
        res = client.post("/api/command", json={"command": "Check system info"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["completed", "failed", "confirmation_required"]

        # Receive streamed events
        events_received = []
        for _ in range(3):
            try:
                evt = websocket.receive_json()
                events_received.append(evt["type"])
            except Exception as e:
                print("WS receive error:", e)

        assert len(events_received) > 0
