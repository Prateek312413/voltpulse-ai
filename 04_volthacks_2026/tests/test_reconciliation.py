"""
Unit tests for Deterministic Late-Telemetry Ingestion, Reconciliation Diffs, and Timeline Replay.
"""

import pytest
import time
from voltpulse.core.reconciler import TelemetryReconciler


def test_reconciler_baseline_and_late_data_injection():
    reconciler = TelemetryReconciler()
    battery_id = "REC-TEST-PACK"

    # Seed 20 baseline cycles (10, 20, 30, ..., 200)
    reconciler.seed_initial_telemetry(battery_id=battery_id, count=20)
    assert len(reconciler.observations[battery_id]) == 20
    assert reconciler.telemetry_versions[battery_id] == 1

    # Ingest late observation for cycle 95 (which sits between cycle 90 and 100)
    obs, res = reconciler.ingest_observation(
        battery_id=battery_id,
        cycle_number=95.0,
        soh_pct=96.1,
        voltage_v=3.70,
        temperature_c=29.0,
        is_late_explicit=True
    )

    assert obs.is_late is True
    assert res is not None
    assert res.late_observations_ingested >= 1
    assert res.total_active_observations == 21

    # Verify chronological ordering
    timeline = reconciler.observations[battery_id]
    cycles = [r.cycle_number for r in timeline]
    assert cycles == sorted(cycles)
    assert 95.0 in cycles


def test_reconciliation_diff_generation():
    reconciler = TelemetryReconciler()
    battery_id = "DIFF-TEST-PACK"
    reconciler.seed_initial_telemetry(battery_id=battery_id, count=15)

    obs, res = reconciler.ingest_observation(
        battery_id=battery_id,
        cycle_number=65.0,
        soh_pct=92.0,  # lower than expected to cause forecast change
        voltage_v=3.62,
        temperature_c=36.0,
        is_late_explicit=True
    )

    assert res is not None
    assert res.diff is not None
    assert res.reconciliation_duration_ms > 0.0
    assert len(reconciler.reconciliation_history) == 1
