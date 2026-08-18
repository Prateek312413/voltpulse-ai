"""
Integration Tests for FastAPI REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["edition"] == "HackSocial 2026"


def test_triage_preview_endpoint(client):
    res = client.post("/api/triage/parse_preview?message_text=Flooding%20in%20basement%20family%20of%204%20trapped")
    assert res.status_code == 200
    data = res.json()
    assert data["urgency_score"] >= 8.0
    assert data["entities"]["headcount"] == 4


def test_submit_sos_endpoint(client):
    payload = {
        "message_text": "Need urgent diabetic insulin for elderly patient at 420 Pine St",
        "sender_name": "Test Citizen",
        "zone_id": "ZONE-TEST"
    }
    res = client.post("/api/triage/submit_sos", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["urgency_score"] >= 7.5
    assert data["primary_category"] == "CRITICAL_MEDICAL"


def test_dashboard_summary_endpoint(client):
    res = client.get("/api/analytics/dashboard_summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_active_sos" in data
    assert "gini_equity_index" in data
    assert "total_supplies_in_stock" in data


def test_bipartite_graph_endpoint(client):
    res = client.get("/api/matching/bipartite_graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]["hubs"]) > 0


def test_mesh_broadcast_and_ledger_verify(client):
    res = client.post("/api/mesh/broadcast", json={
        "payload_type": "SOS_BEACON",
        "payload_data": {"test": "data"},
        "max_hops": 5
    })
    assert res.status_code == 200

    verify_res = client.get("/api/mesh/ledger/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["is_intact"] is True
