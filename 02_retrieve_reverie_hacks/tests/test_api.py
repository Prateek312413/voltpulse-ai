"""
FastAPI REST API Route Tests
"""

import pytest
from fastapi.testclient import TestClient
from run import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "active_models" in data

def test_catalog_endpoint(client):
    res = client.get("/api/models/catalog")
    assert res.status_code == 200
    data = res.json()
    assert "routing_architecture" in data
    assert "supported_flagship_models" in data

def test_pipeline_run_endpoint(client):
    payload = {
        "prompt": "Model the thermodynamic loss in a power converter at 45C with 12A current.",
        "domain": "engineering",
        "human_in_the_loop_mode": False,
        "strict_verification": True
    }
    res = client.post("/api/pipeline/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "pipeline_id" in data
    assert len(data["subtasks"]) >= 2
    assert len(data["stage_traces"]) == 5
    assert data["confidence_score"] >= 0.85

def test_pipeline_run_empty_prompt_error(client):
    payload = {"prompt": "  "}
    res = client.post("/api/pipeline/run", json=payload)
    assert res.status_code == 400

def test_benchmark_endpoint(client):
    res = client.get("/api/pipeline/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert data["total_test_cases"] == 5
    assert len(data["results"]) == 5
