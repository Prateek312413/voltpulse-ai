"""
Pydantic Schemas for Telemetry Ingestion and Retrieval.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime


class TelemetryCreate(BaseModel):
    observation_id: str = Field(..., description="Unique sensor observation ID")
    cycle_number: int = Field(..., gt=0, description="Cycle count number")
    recorded_at: Optional[str] = Field(None, description="Event timestamp (when sensor recorded measurement)")
    voltage: Optional[float] = Field(None, description="Terminal voltage in Volts")
    current: Optional[float] = Field(None, description="Current in Amperes")
    temperature: Optional[float] = Field(None, description="Cell temperature in °C")
    capacity: Optional[float] = Field(None, description="Measured capacity in Ah")
    soh: float = Field(..., description="Observed State-of-Health in range [0.0, 1.2]")


class TelemetryCorrect(BaseModel):
    soh: float = Field(..., description="Corrected SOH value")
    voltage: Optional[float] = None
    current: Optional[float] = None
    temperature: Optional[float] = None
    capacity: Optional[float] = None
    correction_reason: str = Field(..., min_length=3, description="Audit reason for calibration correction")


class TelemetryResponse(BaseModel):
    id: str
    observation_id: str
    battery_id: str
    cycle_number: int
    recorded_at: Optional[str] = None
    received_at: Optional[str] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    temperature: Optional[float] = None
    capacity: Optional[float] = None
    soh: float
    is_active: bool
    replaces_id: Optional[str] = None
    version: int
    telemetry_version: int
    correction_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TelemetryBatchCreate(BaseModel):
    observations: List[TelemetryCreate]
