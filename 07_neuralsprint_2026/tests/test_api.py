"""
API Integration tests for NeuroAccess FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["dsp_pipeline_ready"] is True

def test_aac_vocab_endpoint(client):
    response = client.get("/api/aac-vocab")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert len(data["categories"]) >= 3

def test_restore_speech_endpoint(client):
    payload = {"raw_text_hint": "wtr"}
    response = client.post("/api/restore-speech", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["restored_word"] == "WATER"
    assert data["confidence_score"] > 0.0

def test_predict_intent_endpoint(client):
    payload = {"tokens": ["WATER"], "context": {"hour": 14}}
    response = client.post("/api/predict-intent", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["predictions"]) > 0

def test_sos_trigger_and_incidents(client):
    payload = {
        "trigger_source": "API_TEST",
        "message": "Emergency test message"
    }
    response = client.post("/api/sos-trigger", json=payload)
    assert response.status_code == 200
    sos_data = response.json()
    alert_id = sos_data["alert_id"]

    # Verify in incidents list
    inc_resp = client.get("/api/sos-incidents")
    assert inc_resp.status_code == 200
    inc_data = inc_resp.json()
    assert any(i["alert_id"] == alert_id for i in inc_data["incidents"])

    # Acknowledge incident
    ack_resp = client.post(f"/api/sos-ack/{alert_id}")
    assert ack_resp.status_code == 200
    assert ack_resp.json()["acknowledgment_status"] == "RESOLVED"

def test_run_benchmarks_endpoint(client):
    response = client.get("/api/run-benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASS"
    assert "dsp_latency_ms" in data
    assert "keystroke_reduction_pct" in data
    assert data["keystroke_reduction_pct"] > 80.0

def test_serve_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "NeuroAccess AI" in response.text
    assert "text/html" in response.headers["content-type"]

def test_favicon(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 204
