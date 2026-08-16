"""
Pydantic Schemas for Battery Registry.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class BatteryCreate(BaseModel):
    battery_id: str = Field(..., description="Unique battery identifier", min_length=1, max_length=64)
    battery_type: str = Field(default="Li-ion NMC", description="Battery chemistry or model type")
    nominal_capacity: float = Field(default=2.0, gt=0.0, description="Nominal capacity in Ampere-hours (Ah)")


class BatteryResponse(BaseModel):
    battery_id: str
    battery_type: str
    nominal_capacity: float
    active_telemetry_version: int
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
