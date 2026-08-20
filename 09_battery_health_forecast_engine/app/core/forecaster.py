"""
Uncertainty-Aware SOH Forecast Generator.
Produces versioned predictions with explicit confidence bounds using the selected GPR kernel.
"""

from datetime import datetime, timezone
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from app.core.gpr.kernels import KERNEL_REGISTRY, Kernel
from app.core.gpr.gp_engine import CustomGaussianProcessRegressor
from app.core.temporal import FeaturePipelineConfig
from app.config import settings


class ForecastResult:
    """Stores generated forecast prediction with uncertainty and configuration metadata."""
    def __init__(
        self,
        target_cycle: int,
        predicted_soh: float,
        std_dev: float,
        lower_ci: float,
        upper_ci: float,
        selected_kernel: str,
        hyperparameters: Dict[str, float],
        jitter_used: float,
        noise_variance: float,
        telemetry_version: int,
        forecast_version: int = 1,
        created_at: Optional[datetime] = None,
        multi_horizon_points: Optional[List[Dict[str, Any]]] = None
    ):
        self.target_cycle = target_cycle
        self.predicted_soh = predicted_soh
        self.std_dev = std_dev
        self.lower_ci = lower_ci
        self.upper_ci = upper_ci
        self.selected_kernel = selected_kernel
        self.hyperparameters = hyperparameters
        self.jitter_used = jitter_used
        self.noise_variance = noise_variance
        self.telemetry_version = telemetry_version
        self.forecast_version = forecast_version
        self.created_at = created_at or datetime.now(timezone.utc)
        self.multi_horizon_points = multi_horizon_points or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_cycle": self.target_cycle,
            "predicted_soh": round(self.predicted_soh, 4),
            "std_dev": round(self.std_dev, 4),
            "lower_ci": round(self.lower_ci, 4),
            "upper_ci": round(self.upper_ci, 4),
            "selected_kernel": self.selected_kernel,
            "hyperparameters": self.hyperparameters,
            "jitter_used": self.jitter_used,
            "noise_variance": self.noise_variance,
            "telemetry_version": self.telemetry_version,
            "forecast_version": self.forecast_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "multi_horizon_points": self.multi_horizon_points
        }


def generate_forecast(
    X_train: np.ndarray,
    y_train: np.ndarray,
    pipeline_config: FeaturePipelineConfig,
    target_cycle: int,
    selected_kernel_name: str,
    telemetry_version: int,
    forecast_version: int = 1,
    hyperparameters: Optional[Dict[str, float]] = None,
    generate_curve_to_target: bool = True
) -> ForecastResult:
    """
    Fits the chosen GPR kernel on the entire active dataset and forecasts SOH at target_cycle.
    Optionally computes intermediate horizon points between latest observation and target cycle.
    """
    kernel = KERNEL_REGISTRY.get(selected_kernel_name, KERNEL_REGISTRY["RBF"])
    
    # Instantiate and fit GPR
    model = CustomGaussianProcessRegressor(
        kernel=kernel,
        optimize_hyperparameters=(hyperparameters is None)
    )
    model.fit(X_train, y_train, initial_params=hyperparameters)

    # Prepare query vector for target cycle
    target_dict = {"cycle_number": float(target_cycle)}
    # Fill defaults for other features if multi-feature
    for feat in pipeline_config.feature_names:
        if feat not in target_dict:
            target_dict[feat] = pipeline_config.means.get(feat, 0.0)

    X_query = pipeline_config.transform([target_dict])
    mu, std, lower_ci, upper_ci = model.predict(X_query, return_std=True)

    # Multi-horizon trajectory generation (for visualization curve)
    horizon_points: List[Dict[str, Any]] = []
    if generate_curve_to_target:
        # Determine min and max cycle for continuous curve
        min_cycle = int(min(X_train[:, 0] * pipeline_config.stds.get("cycle_number", 1.0) + pipeline_config.means.get("cycle_number", 0.0))) if len(X_train) > 0 else 1
        max_cycle = max(target_cycle, min_cycle + 50)
        
        cycle_grid = np.linspace(min_cycle, max_cycle, num=100)
        grid_dicts = []
        for c in cycle_grid:
            d = {"cycle_number": float(c)}
            for feat in pipeline_config.feature_names:
                if feat != "cycle_number":
                    d[feat] = pipeline_config.means.get(feat, 0.0)
            grid_dicts.append(d)
            
        X_grid = pipeline_config.transform(grid_dicts)
        mu_g, std_g, low_g, up_g = model.predict(X_grid, return_std=True)
        
        for c, m, s, l, u in zip(cycle_grid, mu_g, std_g, low_g, up_g):
            horizon_points.append({
                "cycle": round(float(c), 1),
                "predicted_soh": round(float(m), 4),
                "std_dev": round(float(s), 4),
                "lower_ci": round(float(l), 4),
                "upper_ci": round(float(u), 4)
            })

    return ForecastResult(
        target_cycle=target_cycle,
        predicted_soh=float(mu[0]),
        std_dev=float(std[0]),
        lower_ci=float(lower_ci[0]),
        upper_ci=float(upper_ci[0]),
        selected_kernel=kernel.name,
        hyperparameters=model.params,
        jitter_used=model.jitter_used,
        noise_variance=model.noise_variance,
        telemetry_version=telemetry_version,
        forecast_version=forecast_version,
        multi_horizon_points=horizon_points
    )
