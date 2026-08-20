"""
Unit tests for Temporal Reconstruction, Lineage Tracking, and Dataset Construction.
"""

from datetime import datetime, timezone, timedelta
import numpy as np
from app.core.temporal import build_active_temporal_dataset, create_temporal_validation_split


def test_event_time_ordering_decoupling():
    """Verifies that arrival order does NOT dictate model training order."""
    now = datetime.now(timezone.utc)
    # Arrived in order: Cycle 20 first, Cycle 10 second, Cycle 5 third
    obs_arrival_order = [
        {"observation_id": "OBS-20", "cycle_number": 20, "recorded_at": (now - timedelta(days=5)).isoformat(), "soh": 0.90, "is_active": True},
        {"observation_id": "OBS-10", "cycle_number": 10, "recorded_at": (now - timedelta(days=15)).isoformat(), "soh": 0.95, "is_active": True},
        {"observation_id": "OBS-05", "cycle_number": 5, "recorded_at": (now - timedelta(days=20)).isoformat(), "soh": 0.98, "is_active": True}
    ]

    sorted_obs, _, X, y = build_active_temporal_dataset(obs_arrival_order)

    # Assert sorted chronologically by cycle: 5, 10, 20
    assert len(sorted_obs) == 3
    assert [o["cycle_number"] for o in sorted_obs] == [5, 10, 20]
    assert [o["soh"] for o in sorted_obs] == [0.98, 0.95, 0.90]


def test_superseded_corrections_exclusion():
    """Verifies that superseded observation versions are excluded from active dataset."""
    obs_list = [
        {"observation_id": "OBS-1", "cycle_number": 1, "soh": 0.80, "is_active": False, "version": 1},
        {"observation_id": "OBS-1", "cycle_number": 1, "soh": 0.99, "is_active": True, "version": 2},
        {"observation_id": "OBS-2", "cycle_number": 2, "soh": 0.98, "is_active": True, "version": 1}
    ]

    sorted_obs, _, X, y = build_active_temporal_dataset(obs_list)
    assert len(sorted_obs) == 2
    assert sorted_obs[0]["soh"] == 0.99
    assert sorted_obs[0]["version"] == 2
    assert sorted_obs[1]["soh"] == 0.98


def test_temporal_validation_split_no_future_leakage():
    """Verifies that temporal validation window is strictly after training window."""
    X = np.arange(100).reshape(-1, 1)
    y = np.linspace(1.0, 0.7, 100)

    X_train, y_train, X_val, y_val = create_temporal_validation_split(X, y, train_ratio=0.75)

    assert len(X_train) == 75
    assert len(X_val) == 25
    # Max train index must be strictly less than min val index
    assert np.max(X_train) < np.min(X_val)
