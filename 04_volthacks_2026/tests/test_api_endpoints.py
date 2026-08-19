"""
Integration tests for FastAPI REST Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure 04_volthacks_2026 is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"


def test_live_telemetry_endpoint():
    response = client.get("/api/telemetry/live")
    assert response.status_code == 200
    data = response.json()
    assert data["pack_voltage_v"] > 40.0
    assert len(data["cells"]) == 16
    assert len(data["can_frames"]) > 0


def test_can_frames_and_modbus_endpoints():
    r1 = client.get("/api/telemetry/can_frames")
    assert r1.status_code == 200
    assert r1.json()["frame_count"] > 0

    r2 = client.get("/api/telemetry/modbus_registers")
    assert r2.status_code == 200
    assert len(r2.json()["registers"]) >= 25


def test_forecast_endpoints():
    r1 = client.get("/api/forecast/latest")
    assert r1.status_code == 200
    data1 = r1.json()
    assert len(data1["forecast_curve"]) > 0

    r2 = client.get("/api/forecast/kernel_benchmark")
    assert r2.status_code == 200
    assert len(r2.json()) == 5


def test_hardware_actuation_and_faults():
    # Toggle load
    r1 = client.post("/api/hardware/set_load_current", json={"current_a": -20.0})
    assert r1.status_code == 200
    assert r1.json()["mode"] == "CHARGING"

    # Inject Thermal Runaway
    r2 = client.post("/api/hardware/fault/thermal_runaway", json={"cell_id": 7, "growth_rate_c_per_sec": 5.0})
    assert r2.status_code == 200
    assert r2.json()["status"] == "FAULT_INJECTED"

    # Clear fault
    r3 = client.post("/api/hardware/fault/clear_thermal")
    assert r3.status_code == 200

    # Contactor reset
    r4 = client.post("/api/hardware/contactor", json={"state": "CLOSED"})
    assert r4.status_code == 200


def test_reconciliation_endpoints():
    req = {
        "battery_id": "BESS-GRID-PACK-01",
        "cycle_number": 125.0,
        "soh_pct": 91.5,
        "voltage_v": 3.66,
        "temperature_c": 32.0,
        "lag_days_simulated": 10.0
    }
    res = client.post("/api/reconciliation/inject_late_observation", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["late_observations_ingested"] >= 1

    r_hist = client.get("/api/reconciliation/history")
    assert r_hist.status_code == 200
    assert len(r_hist.json()) >= 1


def test_analytics_endpoints():
    r1 = client.get("/api/analytics/nyquist_spectrum?soh_pct=95.0&temp_c=25.0")
    assert r1.status_code == 200
    assert len(r1.json()) > 0

    r2 = client.get("/api/analytics/summary_kpis")
    assert r2.status_code == 200
    assert "pack_voltage_v" in r2.json()
