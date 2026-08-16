"""
Unit tests for Late-Telemetry Impact Detection and Reconciliation Diffs.
"""

from app.core.reconciler import detect_affected_forecasts, reconcile_single_forecast
from data.generator import generate_battery_telemetry


def test_detect_affected_forecasts():
    existing_forecasts = [
        {"id": "FC-1", "target_cycle": 50, "forecast_version": 1},
        {"id": "FC-2", "target_cycle": 100, "forecast_version": 1}
    ]

    # Incoming observation for cycle 30 (arrived late after cycle 50 forecast generated)
    incoming_late = [{"observation_id": "OBS-30", "cycle_number": 30}]
    affected = detect_affected_forecasts(existing_forecasts, incoming_late)
    assert len(affected) == 2  # Both target_cycle 50 and 100 are affected

    # Incoming observation for cycle 150 (future)
    incoming_future = [{"observation_id": "OBS-150", "cycle_number": 150}]
    affected_future = detect_affected_forecasts(existing_forecasts, incoming_future)
    assert len(affected_future) == 0


def test_reconciliation_forecast_version_increment_and_diff():
    # Initial 30 observations
    all_obs = generate_battery_telemetry("BAT-TEST-RECON", num_cycles=30)
    for o in all_obs:
        o["is_active"] = True
        o["telemetry_version"] = 1

    old_fc = {
        "id": "FC-BAT-TEST-RECON-C50-v1",
        "forecast_version": 1,
        "predicted_soh": 0.85,
        "std_dev": 0.04,
        "selected_kernel": "RBF"
    }

    # Add a late observation for cycle 15
    late_obs = {
        "observation_id": "OBS-BAT-TEST-RECON-C015",
        "cycle_number": 15,
        "soh": 0.96,
        "voltage": 3.72,
        "current": 1.5,
        "temperature": 26.0,
        "capacity": 1.92,
        "is_active": True,
        "telemetry_version": 2
    }
    all_obs.append(late_obs)

    new_fc, diff = reconcile_single_forecast(
        battery_id="BAT-TEST-RECON",
        target_cycle=50,
        latest_old_forecast=old_fc,
        all_observations=all_obs,
        new_telemetry_version=2,
        triggering_observation_ids=["OBS-BAT-TEST-RECON-C015"]
    )

    assert new_fc.forecast_version == 2
    assert diff is not None
    assert diff.old_forecast_version == 1
    assert diff.new_forecast_version == 2
    assert "OBS-BAT-TEST-RECON-C015" in diff.triggering_observation_ids
