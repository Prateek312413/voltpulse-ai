"""
Pydantic Schemas for Forecasting.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class ForecastRequest(BaseModel):
    target_cycle: int = Field(..., gt=0, description="Future cycle number to forecast SOH for")
    kernel_name: Optional[str] = Field(None, description="Optional override kernel name (defaults to auto-selected best)")
    generate_curve: bool = Field(default=True, description="Whether to compute continuous curve trajectory")


class HorizonPoint(BaseModel):
    cycle: float
    predicted_soh: float
    std_dev: float
    lower_ci: float
    upper_ci: float


class ForecastResponse(BaseModel):
    forecast_id: str
    battery_id: str
    forecast_version: int
    source_telemetry_version: int
    target_cycle: int
    predicted_soh: float
    std_dev: float
    lower_ci: float
    upper_ci: float
    selected_kernel: str
    hyperparameters: Dict[str, float]
    jitter_used: float
    noise_variance: float
    previous_forecast_id: Optional[str] = None
    multi_horizon_points: Optional[List[HorizonPoint]] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
