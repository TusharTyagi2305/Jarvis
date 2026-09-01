import pytest
from fastapi.testclient import TestClient
from jarvis.api.app import app

client = TestClient(app)

def test_api_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"
    assert res.json()["agent"] == "JARVIS Personal Desktop Agent"

def test_api_system_endpoint():
    res = client.get("/api/system")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "cpu_usage_percent" in data["data"]

def test_api_chat_endpoint():
    res = client.post("/api/chat", json={"query": "Get system information"})
    assert res.status_code == 200
    data = res.json()
    assert "user_request" in data
    assert data["user_request"] == "Get system information"
    assert "final_response" in data

def test_api_history_endpoint():
    res = client.get("/api/history")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
