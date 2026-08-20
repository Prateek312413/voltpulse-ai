import pytest
from fastapi.testclient import TestClient
from evidencemesh.main import app


client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "EvidenceMesh"


def test_scenarios_endpoint():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 4
    assert scenarios[0]["id"].startswith("SCENARIO-")


def test_verify_endpoint_and_tamper_check():
    payload = {
        "text_content": "Empagliflozin reduces the risk of sustained decline in eGFR by 28% in chronic kidney disease patients.",
        "domain": "biomedical",
        "prior_skepticism": 0.5,
        "deep_cross_examination": True
    }
    res = client.post("/api/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "proof_certificate" in data
    cert_id = data["proof_certificate"]["certificate_id"]

    # Check tamper endpoint authentic
    t_res = client.post(f"/api/proofs/{cert_id}/tamper-check")
    assert t_res.status_code == 200
    assert t_res.json()["is_valid"] is True

    # Check simulated tamper
    t_corrupt = client.post(f"/api/proofs/{cert_id}/tamper-check?simulated_corrupt_text=corrupt")
    assert t_corrupt.status_code == 200
    assert t_corrupt.json()["is_valid"] is False
