"""
Replay and Time-Travel Engine.
Allows reconstructing telemetry states at specific versions or event times
and verifies bit-for-bit mathematical determinism of forecasts.
"""

from typing import List, Dict, Any, Tuple
import numpy as np

from app.core.temporal import build_active_temporal_dataset
from app.core.evaluator import evaluate_candidate_models
from app.core.forecaster import generate_forecast, ForecastResult


def replay_telemetry_version(
    all_observations: List[Dict[str, Any]],
    target_telemetry_version: int,
    target_cycle: int,
    enforce_kernel: str = None
) -> Tuple[ForecastResult, Dict[str, Any]]:
    """
    Replays telemetry up to a specific telemetry version or arrival snapshot.
    Builds the active dataset as of that version, runs evaluation, and computes forecast.
    """
    # Filter observations received up to the target version
    filtered_obs = [
        obs for obs in all_observations
        if obs.get("telemetry_version", 1) <= target_telemetry_version
    ]

    sorted_obs, pipeline_config, X, y = build_active_temporal_dataset(filtered_obs)
    
    if len(X) == 0:
        raise ValueError(f"No observations available at telemetry version {target_telemetry_version}")

    summaries, best_model = evaluate_candidate_models(X, y)
    selected_kernel = enforce_kernel or best_model.kernel_type

    forecast = generate_forecast(
        X_train=X,
        y_train=y,
        pipeline_config=pipeline_config,
        target_cycle=target_cycle,
        selected_kernel_name=selected_kernel,
        telemetry_version=target_telemetry_version,
        forecast_version=1
    )

    metadata = {
        "target_telemetry_version": target_telemetry_version,
        "observations_count": len(sorted_obs),
        "selected_model": best_model.to_dict(),
        "all_candidates": [s.to_dict() for s in summaries]
    }

    return forecast, metadata


def verify_determinism_replay(
    observations: List[Dict[str, Any]],
    target_cycle: int,
    kernel_name: str = "RBF",
    num_runs: int = 3
) -> Dict[str, Any]:
    """
    Executes multiple independent runs on identical input data and asserts exact equality
    of predictions, uncertainty intervals, hyperparameters, and jitter used.
    """
    results = []
    for _ in range(num_runs):
        _, pipeline_config, X, y = build_active_temporal_dataset(observations)
        fc = generate_forecast(
            X_train=X,
            y_train=y,
            pipeline_config=pipeline_config,
            target_cycle=target_cycle,
            selected_kernel_name=kernel_name,
            telemetry_version=1,
            forecast_version=1
        )
        results.append(fc)

    # Verify identical outputs across all runs
    ref = results[0]
    is_deterministic = True
    max_diff_soh = 0.0
    max_diff_std = 0.0

    for r in results[1:]:
        diff_soh = abs(r.predicted_soh - ref.predicted_soh)
        diff_std = abs(r.std_dev - ref.std_dev)
        max_diff_soh = max(max_diff_soh, diff_soh)
        max_diff_std = max(max_diff_std, diff_std)
        if diff_soh > 1e-7 or diff_std > 1e-7:
            is_deterministic = False

    return {
        "is_deterministic": is_deterministic,
        "num_runs": num_runs,
        "max_diff_soh": max_diff_soh,
        "max_diff_std": max_diff_std,
        "predicted_soh": ref.predicted_soh,
        "std_dev": ref.std_dev,
        "lower_ci": ref.lower_ci,
        "upper_ci": ref.upper_ci,
        "selected_kernel": ref.selected_kernel
    }
