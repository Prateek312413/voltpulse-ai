"""
Unit tests for Replay Determinism and Time-Travel.
"""

from app.core.replay import verify_determinism_replay, replay_telemetry_version
from data.generator import generate_battery_telemetry


def test_bit_for_bit_determinism_replay():
    obs = generate_battery_telemetry("BAT-DETERMINISM", num_cycles=25)
    for o in obs:
        o["is_active"] = True
        o["telemetry_version"] = 1

    res = verify_determinism_replay(obs, target_cycle=40, kernel_name="RBF", num_runs=3)

    assert res["is_deterministic"] is True
    assert res["max_diff_soh"] == 0.0 or res["max_diff_soh"] < 1e-7
    assert res["max_diff_std"] == 0.0 or res["max_diff_std"] < 1e-7


def test_time_travel_historical_snapshot():
    # Observations arriving across version 1 and version 2
    obs1 = generate_battery_telemetry("BAT-TT", num_cycles=20)
    for o in obs1:
        o["is_active"] = True
        o["telemetry_version"] = 1

    obs2 = generate_battery_telemetry("BAT-TT", num_cycles=40)
    for idx, o in enumerate(obs2):
        o["is_active"] = True
        o["telemetry_version"] = 1 if idx < 20 else 2

    # Time-travel to telemetry version 1 (should only use first 20 observations)
    fc_v1, meta_v1 = replay_telemetry_version(obs2, target_telemetry_version=1, target_cycle=25, enforce_kernel="RBF")
    assert meta_v1["observations_count"] == 20

    # Time-travel to telemetry version 2 (should use all 40 observations)
    fc_v2, meta_v2 = replay_telemetry_version(obs2, target_telemetry_version=2, target_cycle=25, enforce_kernel="RBF")
    assert meta_v2["observations_count"] == 40
    assert fc_v1.predicted_soh is not None
    assert fc_v2.predicted_soh is not None
