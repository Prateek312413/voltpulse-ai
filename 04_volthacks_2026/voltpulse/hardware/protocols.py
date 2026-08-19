"""
CAN-bus (SAE J1939), Modbus TCP, and Telemetry Data Schemas for VoltPulse AI.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import time


class BatteryChemistry(str, Enum):
    NMC_811 = "NMC_811"
    LFP = "LFP"
    SOLID_STATE = "SOLID_STATE"
    NCA = "NCA"


class ContactorState(str, Enum):
    CLOSED = "CLOSED"         # Normal operation, pack connected
    OPEN = "OPEN"             # Idle / Standby
    FAULT_TRIPPED = "FAULT_TRIPPED"  # Emergency hardware disconnect


class BalancingState(str, Enum):
    IDLE = "IDLE"
    ACTIVE_BLEEDING = "ACTIVE_BLEEDING"
    CHARGE_SHUTTLING = "CHARGE_SHUTTLING"


class CellTelemetry(BaseModel):
    cell_id: int = Field(..., ge=1, le=16, description="Cell index 1-16")
    voltage_v: float = Field(..., ge=1.5, le=5.0, description="Cell terminal voltage")
    temperature_c: float = Field(..., ge=-40.0, le=120.0, description="Cell temperature")
    soc_pct: float = Field(..., ge=0.0, le=100.0, description="State of Charge percentage")
    internal_resistance_mohm: float = Field(..., ge=0.1, le=200.0, description="AC internal resistance in mOhm")
    is_balancing: bool = False


class CANFrame(BaseModel):
    timestamp_ms: int
    arbitration_id: int  # 29-bit Extended CAN Identifier (SAE J1939)
    pgn: int
    dlc: int = 8
    data_hex: str        # 16-hex characters representation (e.g. '0x0E4C012A...')
    payload_bytes: List[int]
    description: str


class ModbusRegisterBlock(BaseModel):
    transaction_id: int
    protocol_id: int = 0
    unit_id: int = 1
    start_register: int = 40001
    registers: List[int]  # 16-bit integer words


class PackTelemetryFrame(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    iso_timestamp: str
    pack_id: str = "BESS-GRID-PACK-01"
    chemistry: BatteryChemistry = BatteryChemistry.NMC_811
    nominal_capacity_ah: float = 100.0
    pack_voltage_v: float
    pack_current_a: float  # Positive = Discharging, Negative = Charging
    pack_power_kw: float
    pack_soc_pct: float
    pack_soh_pct: float
    max_cell_voltage_v: float
    min_cell_voltage_v: float
    cell_voltage_delta_mv: float
    max_cell_temp_c: float
    min_cell_temp_c: float
    ambient_temp_c: float
    contactor_status: ContactorState = ContactorState.CLOSED
    balancing_status: BalancingState = BalancingState.IDLE
    cells: List[CellTelemetry]
    can_frames: List[CANFrame] = []
    is_late_telemetry: bool = False
    sequence_id: int = 0
