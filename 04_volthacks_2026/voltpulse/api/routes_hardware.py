"""
API Routes for Hardware Actuation, Contactor Interlocks, and Fault Injections.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from ..core.state import state
from ..hardware.protocols import ContactorState, BalancingState
from ..core.active_balancer import BalancingDecision

router = APIRouter(prefix="/api/hardware", tags=["Hardware Actuation"])


class ContactorRequest(BaseModel):
    state: ContactorState


class LoadCurrentRequest(BaseModel):
    current_a: float  # + = Discharge, - = Charge


class ThermalFaultRequest(BaseModel):
    cell_id: int = 7
    growth_rate_c_per_sec: float = 4.5


class ImbalanceFaultRequest(BaseModel):
    cell_id: int = 4
    soc_drop_pct: float = 25.0


class BalancingRequest(BaseModel):
    state: BalancingState
    cell_ids: List[int] = []


@router.post("/contactor")
def set_contactor_state(req: ContactorRequest):
    """Actuate or reset the high-voltage main contactor relay."""
    state.emulator.set_contactor(req.state)
    return {
        "status": "SUCCESS",
        "contactor_state": state.emulator.contactor_state.value,
        "message": f"Contactor commanded to {req.state.value}"
    }


@router.post("/set_load_current")
def set_load_current(req: LoadCurrentRequest):
    """Set pack load current in Amperes."""
    state.emulator.set_current(req.current_a)
    return {
        "status": "SUCCESS",
        "current_a": req.current_a,
        "mode": "DISCHARGING" if req.current_a > 0 else ("CHARGING" if req.current_a < 0 else "IDLE")
    }


@router.post("/fault/thermal_runaway")
def inject_thermal_runaway(req: ThermalFaultRequest):
    """Inject localized thermal runaway fault on target cell."""
    state.emulator.inject_thermal_runaway(
        cell_id=req.cell_id,
        growth_rate_c_per_sec=req.growth_rate_c_per_sec
    )
    return {
        "status": "FAULT_INJECTED",
        "target_cell": req.cell_id,
        "growth_rate_c_per_sec": req.growth_rate_c_per_sec,
        "warning": "CRITICAL: Thermal runaway gradient active. Surveillance detector will initiate emergency contactor trip."
    }


@router.post("/fault/clear_thermal")
def clear_thermal_fault():
    """Clear thermal runaway fault and reset cell temperatures."""
    state.emulator.clear_thermal_fault()
    return {
        "status": "SUCCESS",
        "message": "Thermal fault cleared. Pack temperatures normalized."
    }


@router.post("/fault/cell_imbalance")
def inject_cell_imbalance(req: ImbalanceFaultRequest):
    """Inject severe State-of-Charge imbalance on a specific cell."""
    state.emulator.inject_cell_imbalance(
        cell_id=req.cell_id,
        soc_drop_pct=req.soc_drop_pct
    )
    return {
        "status": "FAULT_INJECTED",
        "target_cell": req.cell_id,
        "soc_drop_pct": req.soc_drop_pct,
        "message": "Cell imbalance injected. Active balancer will detect delta spread."
    }


@router.post("/fault/sensor_noise")
def toggle_sensor_noise(enabled: bool):
    """Toggle sensor measurement jitter/noise."""
    state.emulator.set_sensor_noise(enabled)
    return {
        "status": "SUCCESS",
        "sensor_noise_active": enabled
    }


@router.post("/trigger_balancing", response_model=BalancingDecision)
def trigger_balancing(req: Optional[BalancingRequest] = None):
    """
    Trigger cell balancing. If cell_ids are empty, automatically evaluates
    which cells exceed the voltage threshold.
    """
    frame = state.emulator.step(dt=0.1)
    decision = state.balancer.evaluate_pack(frame.cells)

    if req and req.cell_ids:
        target_cells = req.cell_ids
        target_state = req.state
    else:
        target_cells = decision.target_cells_to_balance
        target_state = decision.balancing_state

    state.emulator.set_balancing(target_state, target_cells)
    return decision
