"""
FastAPI REST Endpoints Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from aegismed.main import app
from aegismed.database.connection import init_db
from aegismed.database.seed_data import seed_all

@pytest.fixture(scope="module", autouse=True)
def setup_api_db():
    init_db()
    seed_all()

client = TestClient(app)


def test_status_endpoint():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert "metrics" in data
    assert data["metrics"]["total_patients"] >= 3


def test_patients_list_endpoint():
    res = client.get("/api/patients")
    assert res.status_code == 200
    data = res.json()
    assert len(data["patients"]) >= 3
    uids = [p["patient_uid"] for p in data["patients"]]
    assert "P-1001" in uids


def test_patient_details_endpoint():
    res = client.get("/api/patients/P-1001")
    assert res.status_code == 200
    data = res.json()
    assert data["patient"]["name"] == "Marcus Vance"
    assert len(data["episodes"]) >= 2


def test_memory_graph_endpoint():
    res = client.get("/api/memory/graph/P-1001")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["active_memory_count"] > 0


def test_vector_search_endpoint():
    res = client.post("/api/memory/vector-search", json={
        "patient_uid": "P-1001",
        "query_text": "allergic reaction and swelling",
        "top_k": 2
    })
    assert res.status_code == 200
    data = res.json()
    assert "recalled_memories" in data
    assert len(data["recalled_memories"]) > 0
