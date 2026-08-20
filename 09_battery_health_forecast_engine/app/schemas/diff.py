"""
Pydantic Schemas for Forecast Diffs and Reconciliation.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ForecastDiffResponse(BaseModel):
    id: str
    battery_id: str
    target_cycle: int
    old_forecast_id: Optional[str] = None
    old_forecast_version: int
    new_forecast_id: str
    new_forecast_version: int
    old_soh: float
    new_soh: float
    delta_soh: float
    old_std: float
    new_std: float
    delta_std: float
    old_kernel: str
    new_kernel: str
    kernel_changed: bool
    triggering_observation_ids: List[str]
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
