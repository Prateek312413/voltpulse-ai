"""
Late-Telemetry Reconciliation and Forecast Diff Engine.
Detects affected forecasts upon out-of-order or corrected measurement arrival,
evaluates new model configurations, increments forecast versions, and produces semantic diffs.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np

from app.core.temporal import build_active_temporal_dataset
from app.core.evaluator import evaluate_candidate_models
from app.core.forecaster import generate_forecast, ForecastResult


class SemanticForecastDiff:
    """Represents the semantic difference between two forecast versions."""
    def __init__(
        self,
        battery_id: str,
        target_cycle: int,
        old_forecast_id: Optional[str],
        old_forecast_version: int,
        new_forecast_id: str,
        new_forecast_version: int,
        old_soh: float,
        new_soh: float,
        delta_soh: float,
        old_std: float,
        new_std: float,
        delta_std: float,
        old_kernel: str,
        new_kernel: str,
        kernel_changed: bool,
        triggering_observation_ids: List[str],
        reconciliation_timestamp: Optional[datetime] = None
    ):
        self.battery_id = battery_id
        self.target_cycle = target_cycle
        self.old_forecast_id = old_forecast_id
        self.old_forecast_version = old_forecast_version
        self.new_forecast_id = new_forecast_id
        self.new_forecast_version = new_forecast_version
        self.old_soh = old_soh
        self.new_soh = new_soh
        self.delta_soh = delta_soh
        self.old_std = old_std
        self.new_std = new_std
        self.delta_std = delta_std
        self.old_kernel = old_kernel
        self.new_kernel = new_kernel
        self.kernel_changed = kernel_changed
        self.triggering_observation_ids = triggering_observation_ids
        self.reconciliation_timestamp = reconciliation_timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "battery_id": self.battery_id,
            "target_cycle": self.target_cycle,
            "old_forecast_id": self.old_forecast_id,
            "old_forecast_version": self.old_forecast_version,
            "new_forecast_id": self.new_forecast_id,
            "new_forecast_version": self.new_forecast_version,
            "old_soh": round(self.old_soh, 4),
            "new_soh": round(self.new_soh, 4),
            "delta_soh": round(self.delta_soh, 4),
            "old_std": round(self.old_std, 4),
            "new_std": round(self.new_std, 4),
            "delta_std": round(self.delta_std, 4),
            "old_kernel": self.old_kernel,
            "new_kernel": self.new_kernel,
            "kernel_changed": self.kernel_changed,
            "triggering_observation_ids": self.triggering_observation_ids,
            "reconciliation_timestamp": self.reconciliation_timestamp.isoformat()
        }


def detect_affected_forecasts(
    existing_forecasts: List[Dict[str, Any]],
    new_or_modified_observations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Identifies which existing forecasts need reconciliation based on newly arrived observations.
    Any forecast whose target cycle is >= min(new observation cycles) or affected by corrections is flagged.
    """
    if not existing_forecasts or not new_or_modified_observations:
        return []

    min_incoming_cycle = min(obs["cycle_number"] for obs in new_or_modified_observations)
    
    affected = []
    for fc in existing_forecasts:
        # If target cycle is in the future relative to the incoming observation, it is affected
        if fc.get("target_cycle", 0) >= min_incoming_cycle:
            affected.append(fc)

    return affected


def reconcile_single_forecast(
    battery_id: str,
    target_cycle: int,
    latest_old_forecast: Optional[Dict[str, Any]],
    all_observations: List[Dict[str, Any]],
    new_telemetry_version: int,
    triggering_observation_ids: List[str]
) -> Tuple[ForecastResult, Optional[SemanticForecastDiff]]:
    """
    Performs reconciliation for a specific target cycle:
    1. Rebuilds active temporal dataset.
    2. Runs deterministic model evaluation to select best kernel.
    3. Produces new forecast version.
    4. Computes semantic diff against old forecast version.
    """
    # 1. Build dataset
    sorted_obs, pipeline_config, X, y = build_active_temporal_dataset(all_observations)
    
    # 2. Select model
    summaries, best_model = evaluate_candidate_models(X, y)
    
    # 3. New forecast version calculation
    old_version = latest_old_forecast.get("forecast_version", 1) if latest_old_forecast else 0
    new_version = old_version + 1
    
    new_forecast = generate_forecast(
        X_train=X,
        y_train=y,
        pipeline_config=pipeline_config,
        target_cycle=target_cycle,
        selected_kernel_name=best_model.kernel_type,
        telemetry_version=new_telemetry_version,
        forecast_version=new_version
    )

    # 4. Generate Diff if old forecast existed
    diff = None
    if latest_old_forecast:
        old_soh = float(latest_old_forecast.get("predicted_soh", 0.0))
        new_soh = new_forecast.predicted_soh
        delta_soh = new_soh - old_soh
        
        old_std = float(latest_old_forecast.get("std_dev", 0.0))
        new_std = new_forecast.std_dev
        delta_std = new_std - old_std
        
        old_kernel = latest_old_forecast.get("selected_kernel", "")
        new_kernel = new_forecast.selected_kernel
        
        diff = SemanticForecastDiff(
            battery_id=battery_id,
            target_cycle=target_cycle,
            old_forecast_id=latest_old_forecast.get("id"),
            old_forecast_version=old_version,
            new_forecast_id=f"FC-{battery_id}-C{target_cycle}-v{new_version}",
            new_forecast_version=new_version,
            old_soh=old_soh,
            new_soh=new_soh,
            delta_soh=delta_soh,
            old_std=old_std,
            new_std=new_std,
            delta_std=delta_std,
            old_kernel=old_kernel,
            new_kernel=new_kernel,
            kernel_changed=(old_kernel != new_kernel),
            triggering_observation_ids=triggering_observation_ids
        )

    return new_forecast, diff
