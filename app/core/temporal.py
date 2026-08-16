"""
Temporal Reconstruction, Feature Pipeline, and Active Dataset Builder.
Decouples arrival time from event time, maintains correction lineages, and prepares deterministic training windows.
"""

from datetime import datetime, timezone
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings


class FeaturePipelineConfig:
    """Stores deterministic feature scaling parameters for reproducible inference."""
    def __init__(
        self,
        feature_names: List[str],
        means: Dict[str, float],
        stds: Dict[str, float],
        target_name: str = "soh"
    ):
        self.feature_names = feature_names
        self.means = means
        self.stds = stds
        self.target_name = target_name

    def transform(self, rows: List[Dict[str, Any]]) -> np.ndarray:
        """Transforms raw telemetry dictionaries into scaled numpy matrix."""
        matrix = []
        for row in rows:
            feat_vec = []
            for name in self.feature_names:
                val = float(row.get(name, 0.0) or 0.0)
                mean = self.means.get(name, 0.0)
                std = self.stds.get(name, 1.0)
                std = std if std > 1e-8 else 1.0
                feat_vec.append((val - mean) / std)
            matrix.append(feat_vec)
        return np.asarray(matrix, dtype=np.float64)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_names": self.feature_names,
            "means": self.means,
            "stds": self.stds,
            "target_name": self.target_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeaturePipelineConfig":
        return cls(
            feature_names=data["feature_names"],
            means=data["means"],
            stds=data["stds"],
            target_name=data.get("target_name", "soh")
        )


def build_active_temporal_dataset(
    observations: List[Dict[str, Any]],
    multi_feature: bool = False
) -> Tuple[List[Dict[str, Any]], FeaturePipelineConfig, np.ndarray, np.ndarray]:
    """
    Builds the active, temporally ordered dataset from a list of observations.
    
    Rules:
    1. Filter only active observations (is_active == True, excluding superseded versions).
    2. Sort deterministically by event timeline: (cycle_number ASC, recorded_at ASC, id ASC).
    3. Construct deterministic feature scaling parameters.
    4. Return (active_sorted_records, pipeline_config, X_matrix, y_vector).
    """
    # 1. Filter active only
    active_obs = [obs for obs in observations if obs.get("is_active", True)]

    # 2. Sort by event timeline (cycle_number, then recorded_at, then observation_id for stability)
    def _sort_key(obs: Dict[str, Any]):
        cycle = obs.get("cycle_number", 0)
        rec_at = obs.get("recorded_at")
        if isinstance(rec_at, str):
            rec_str = rec_at
        elif isinstance(rec_at, datetime):
            rec_str = rec_at.isoformat()
        else:
            rec_str = ""
        obs_id = obs.get("id", obs.get("observation_id", ""))
        return (cycle, rec_str, obs_id)

    sorted_obs = sorted(active_obs, key=_sort_key)

    if not sorted_obs:
        empty_config = FeaturePipelineConfig(feature_names=["cycle_number"], means={"cycle_number": 0.0}, stds={"cycle_number": 1.0})
        return [], empty_config, np.empty((0, 1)), np.empty(0)

    # 3. Choose features
    if multi_feature:
        feature_names = ["cycle_number", "voltage", "current", "temperature", "capacity"]
    else:
        feature_names = ["cycle_number"]

    # Compute means and standard deviations
    means = {}
    stds = {}
    for feat in feature_names:
        vals = [float(obs.get(feat, 0.0) or 0.0) for obs in sorted_obs]
        arr = np.asarray(vals, dtype=np.float64)
        means[feat] = float(np.mean(arr))
        s = float(np.std(arr))
        stds[feat] = s if s > 1e-6 else 1.0

    pipeline_config = FeaturePipelineConfig(
        feature_names=feature_names,
        means=means,
        stds=stds,
        target_name="soh"
    )

    X = pipeline_config.transform(sorted_obs)
    y = np.asarray([float(obs["soh"]) for obs in sorted_obs], dtype=np.float64)

    return sorted_obs, pipeline_config, X, y


def create_temporal_validation_split(
    X: np.ndarray,
    y: np.ndarray,
    train_ratio: float = 0.75
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Creates a deterministic temporal validation split.
    Guarantees no future leakage: training window is strictly before validation window.
    """
    N = X.shape[0]
    if N < 4:
        # If very small dataset, use all for train and evaluate on train to prevent crash
        return X, y, X, y

    split_idx = int(np.floor(N * train_ratio))
    split_idx = max(2, min(split_idx, N - 1))

    X_train = X[:split_idx]
    y_train = y[:split_idx]
    X_val = X[split_idx:]
    y_val = y[split_idx:]

    return X_train, y_train, X_val, y_val
