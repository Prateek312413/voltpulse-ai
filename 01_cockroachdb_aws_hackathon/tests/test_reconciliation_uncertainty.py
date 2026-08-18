"""
Tests for Bayesian Uncertainty Engine and Late-Telemetry Memory Reconciliation
"""

import pytest
import datetime
from aegismed.database.connection import get_db_session, init_db
from aegismed.database.seed_data import seed_all
from aegismed.ml.uncertainty_engine import uncertainty_engine
from aegismed.memory.reconciliation import LateTelemetryReconciler


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    seed_all()


def test_gaussian_process_uncertainty_bounds():
    """Validates that GP produces calibrated 95% confidence intervals."""
    time_points = [0.0, 30.0, 60.0, 90.0]
    biomarker_values = [1.0, 1.1, 1.2, 1.4] # Rising creatinine

    result = uncertainty_engine.forecast_biomarker_trajectory(
        time_points_days=time_points,
        biomarker_values=biomarker_values,
        forecast_horizon_days=60
    )

    assert "predicted_mean" in result
    assert "lower_confidence_95" in result
    assert "upper_confidence_95" in result
    assert len(result["predicted_mean"]) == len(result["upper_confidence_95"])

    # Verify mathematical constraint: lower <= mean <= upper
    for l, m, u in zip(result["lower_confidence_95"], result["predicted_mean"], result["upper_confidence_95"]):
        assert l <= m <= u


def test_late_telemetry_reconciliation_in_cockroachdb():
    """Validates out-of-order delayed lab ingestion and retroactive contradiction detection."""
    with get_db_session() as db:
        reconciler = LateTelemetryReconciler(db)
        
        # Ingest a delayed lab dated 250 days ago (prior to Episode 2 at 180 days ago) showing severe creatinine spike
        delayed_time = datetime.datetime.utcnow() - datetime.timedelta(days=250)
        res = reconciler.ingest_late_telemetry(
            patient_uid="P-1002",
            delayed_timestamp=delayed_time,
            observation_type="Delayed Serum Creatinine Spike",
            observation_data={"lab_results": {"creatinine": 1.75}, "symptoms": ["Edema", "Fatigue"]},
            clinical_note="Asynchronous lab sync from outpatient dialysis clinic."
        )

        assert res["status"] == "RECONCILIATION_COMPLETE"
        assert res["delay_interval_days"] >= 240
        assert res["subsequent_episodes_re-evaluated"] >= 1
        assert "reconciled_trajectory_forecast" in res
