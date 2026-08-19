"""
API Routes for Real-Time 16-Cell Telemetry, CAN-bus frames, and Modbus TCP.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import time

from ..core.state import state
from ..hardware.protocols import PackTelemetryFrame, ContactorState

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("/live", response_model=PackTelemetryFrame)
def get_live_telemetry(dt: float = 0.5):
    """
    Fetch the latest live 16-cell series pack telemetry frame,
    advances the physics simulation, and evaluates thermal safety.
    """
    frame = state.emulator.step(dt=dt)

    # Convert cells to format for thermal detector
    cells_raw = [
        {"cell_id": c.cell_id, "voltage_v": c.voltage_v, "temperature_c": c.temperature_c}
        for c in frame.cells
    ]
    safety_report = state.thermal_detector.analyze_frame(timestamp=frame.timestamp, cell_data=cells_raw)

    # Automatic Hardware Interlock Trip if critical runaway
    if safety_report.contactor_trip_recommended and state.emulator.contactor_state == ContactorState.CLOSED:
        state.emulator.set_contactor(ContactorState.FAULT_TRIPPED)
        frame.contactor_status = ContactorState.FAULT_TRIPPED

    # Evaluate balancing
    balancing_decision = state.balancer.evaluate_pack(frame.cells)
    if balancing_decision.contactor_interlock_trip and state.emulator.contactor_state == ContactorState.CLOSED:
        state.emulator.set_contactor(ContactorState.FAULT_TRIPPED)
        frame.contactor_status = ContactorState.FAULT_TRIPPED

    return frame


@router.get("/can_frames")
def get_recent_can_frames():
    """Retrieve raw J1939 CAN-bus hexadecimal frames."""
    frame = state.emulator.step(dt=0.1)
    return {
        "timestamp_ms": int(time.time() * 1000),
        "frame_count": len(frame.can_frames),
        "frames": frame.can_frames
    }


@router.get("/modbus_registers")
def get_modbus_tcp_registers():
    """Retrieve 16-bit Modbus TCP register map for PLC integration."""
    frame = state.emulator.step(dt=0.1)
    modbus_block = state.emulator.generate_modbus_registers(frame)
    return modbus_block
