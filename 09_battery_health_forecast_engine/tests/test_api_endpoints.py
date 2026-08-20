"""
Comprehensive FastAPI API Endpoint Tests for Battery Health Forecast Engine.
Validates all REST endpoints defined in PRD Functional Requirements.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    init_db()


def test_battery_lifecycle_endpoints():
    bat_id = f"BAT-API-{uuid.uuid4().hex[:8]}"
    # 1. Create battery
    res = client.post("/batteries", json={
        "battery_id": bat_id,
        "battery_type": "Li-ion NMC",
        "nominal_capacity": 2.2
    })
    assert res.status_code in [200, 201]
    data = res.json()
    assert data["battery_id"] == bat_id
    assert data["active_telemetry_version"] == 1

    # 2. Duplicate battery rejection (409 Conflict)
    dup_res = client.post("/batteries", json={
        "battery_id": bat_id,
        "battery_type": "Li-ion NMC",
        "nominal_capacity": 2.2
    })
    assert dup_res.status_code == 409

    # 3. Retrieve battery metadata
    get_res = client.get(f"/batteries/{bat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["battery_id"] == bat_id

    # 4. List batteries
    list_res = client.get("/batteries")
    assert list_res.status_code == 200
    assert any(b["battery_id"] == bat_id for b in list_res.json())


def test_telemetry_ingestion_and_retrieval_endpoints():
    bat_id = f"BAT-TEL-{uuid.uuid4().hex[:8]}"
    client.post("/batteries", json={"battery_id": bat_id, "battery_type": "Li-ion LFP", "nominal_capacity": 2.0})

    # Ingest single observation
    obs_res = client.post(f"/batteries/{bat_id}/observations", json={
        "observation_id": "OBS-01",
        "cycle_number": 1,
        "recorded_at": "2026-08-15T09:00:00Z",
        "voltage": 3.75,
        "current": 1.5,
        "temperature": 25.0,
        "capacity": 2.0,
        "soh": 1.0
    })
    assert obs_res.status_code in [200, 201]
    assert obs_res.json()["observation_id"] == "OBS-01"

    # Ingest batch
    batch_res = client.post(f"/batteries/{bat_id}/observations/batch", json={"observations": [
        {
            "observation_id": "OBS-02",
            "cycle_number": 2,
            "recorded_at": "2026-08-15T13:00:00Z",
            "voltage": 3.74,
            "current": 1.5,
            "temperature": 25.5,
            "capacity": 1.99,
            "soh": 0.995
        },
        {
            "observation_id": "OBS-03",
            "cycle_number": 3,
            "recorded_at": "2026-08-15T17:00:00Z",
            "voltage": 3.73,
            "current": 1.5,
            "temperature": 26.0,
            "capacity": 1.98,
            "soh": 0.990
        }
    ]})
    assert batch_res.status_code in [200, 201]
    assert len(batch_res.json()) == 2

    # Retrieval in event-time order
    event_res = client.get(f"/batteries/{bat_id}/observations?order_by=event_time")
    assert event_res.status_code == 200
    assert len(event_res.json()) == 3
    assert event_res.json()[0]["cycle_number"] == 1

    # Retrieval in receive-time order
    recv_res = client.get(f"/batteries/{bat_id}/observations?order_by=receive_time")
    assert recv_res.status_code == 200
    assert len(recv_res.json()) == 3


def test_observation_correction_endpoint():
    bat_id = f"BAT-CORR-{uuid.uuid4().hex[:8]}"
    client.post("/batteries", json={"battery_id": bat_id, "battery_type": "Li-ion LFP", "nominal_capacity": 2.0})

    client.post(f"/batteries/{bat_id}/observations", json={
        "observation_id": "OBS-CORR-1",
        "cycle_number": 10,
        "recorded_at": "2026-08-15T09:00:00Z",
        "voltage": 3.60,
        "current": 1.5,
        "temperature": 28.0,
        "capacity": 1.70,
        "soh": 0.85
    })

    # Correct observation
    corr_res = client.post(f"/batteries/{bat_id}/observations/OBS-CORR-1/correct", json={
        "soh": 0.96,
        "voltage": 3.72,
        "current": 1.5,
        "temperature": 25.0,
        "capacity": 1.92,
        "correction_reason": "Sensor thermal drift recalibration"
    })
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["soh"] == 0.96
    assert corr_data["version"] == 2
    assert corr_data["correction_reason"] == "Sensor thermal drift recalibration"


def test_model_evaluation_and_forecast_endpoints():
    bat_id = f"BAT-FC-{uuid.uuid4().hex[:8]}"
    client.post("/batteries", json={"battery_id": bat_id, "battery_type": "Li-ion NMC", "nominal_capacity": 2.0})

    # Add 20 observations
    from data.generator import generate_battery_telemetry
    obs_list = generate_battery_telemetry(bat_id, num_cycles=20)
    client.post(f"/batteries/{bat_id}/observations/batch", json={"observations": obs_list})

    # Evaluate models
    eval_res = client.post(f"/batteries/{bat_id}/models/evaluate", json={"target_coverage": 0.95})
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "all_candidates" in eval_data
    assert "selected_model" in eval_data
    assert eval_data["selected_model"]["status"] == "SUCCESS"

    # Generate forecast
    fc_res = client.post(f"/batteries/{bat_id}/forecasts", json={
        "target_cycle": 50,
        "kernel_override": "Matern52"
    })
    assert fc_res.status_code in [200, 201]
    fc_data = fc_res.json()
    assert fc_data["target_cycle"] == 50
    assert "predicted_soh" in fc_data
    assert "std_dev" in fc_data
    assert "lower_ci" in fc_data
    assert "upper_ci" in fc_data
    assert fc_data["lower_ci"] < fc_data["predicted_soh"] < fc_data["upper_ci"]

    # Retrieve forecasts list
    fc_list_res = client.get(f"/batteries/{bat_id}/forecasts")
    assert fc_list_res.status_code == 200
    assert len(fc_list_res.json()) >= 1


def test_scenarios_endpoints():
    list_res = client.get("/scenarios/list")
    assert list_res.status_code == 200
    scenarios = list_res.json()
    assert len(scenarios) == 12

    for i in range(1, 13):
        run_res = client.post(f"/scenarios/run/{i}")
        assert run_res.status_code == 200
        assert run_res.json()["passed"] is True
