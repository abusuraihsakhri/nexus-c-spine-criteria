"""API contract and legacy isolation."""
import pytest
from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").status_code == 200


def test_nexus_negative_api():
    payload = {key: False for key in (
        "midline_tenderness", "intoxication", "altered_alertness",
        "focal_neurologic_deficit", "distracting_injury"
    )}
    response = client.post("/api/nexus", json=payload)
    assert response.status_code == 200
    assert response.json()["classification"] == "NEXUS_NEGATIVE"


def test_nexus_incomplete_api():
    response = client.post("/api/nexus", json={})
    assert response.status_code == 200
    assert response.json()["classification"] == "INCOMPLETE"


def test_age_rejected():
    assert client.post("/api/nexus", json={"age": 121}).status_code == 422


def test_legacy_logs_off_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LEGACY_API", raising=False)
    monkeypatch.delenv("LEGACY_API_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 404


def test_legacy_api_requires_token(monkeypatch):
    monkeypatch.setenv("ENABLE_LEGACY_API", "1")
    monkeypatch.setenv("LEGACY_API_TOKEN", "example-test-only-key")
    assert client.get("/api/audit/logs").status_code == 401
    assert client.get("/api/audit/logs", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/api/audit/logs", headers={"X-API-Key": "example-test-only-key"}).status_code == 200


def test_unknown_criterion_rejected():
    assert client.post("/api/nexus", json={"alertness": False}).status_code == 422
