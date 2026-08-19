"""
API Routes for Out-of-Order Telemetry Injection, Reconciliation Diffs, and Timeline Auditing.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import time

from ..core.state import state
from ..core.reconciler import ObservationRecord, ReconciliationResult

router = APIRouter(prefix="/api/reconciliation", tags=["Late-Telemetry Reconciliation"])


class LateObservationRequest(BaseModel):
    battery_id: str = "BESS-GRID-PACK-01"
    cycle_number: float = 140.0
    soh_pct: float = 88.2
    voltage_v: float = 3.65
    temperature_c: float = 34.2
    lag_days_simulated: float = 14.0


@router.get("/history", response_model=List[ReconciliationResult])
def get_reconciliation_history():
    """Retrieve full audit ledger of historical reconciliation events and parameter diffs."""
    return state.reconciler.reconciliation_history


@router.get("/observations", response_model=List[ObservationRecord])
def get_observations(
    battery_id: str = "BESS-GRID-PACK-01",
    order_by: str = Query("cycle", enum=["cycle", "received_at"])
):
    """
    Retrieve all persisted telemetry observations.
    Allows toggling between event-time (cycle) and receive-time ordering.
    """
    obs = state.reconciler.observations.get(battery_id, [])
    if order_by == "received_at":
        return sorted(obs, key=lambda r: r.received_at)
    return sorted(obs, key=lambda r: (r.cycle_number, r.recorded_at))


@router.post("/inject_late_observation", response_model=ReconciliationResult)
def inject_late_telemetry(req: LateObservationRequest):
    """
    Simulate an asynchronous IoT packet arriving days late.
    Triggers timeline reconstruction, GPR re-training, and diff generation.
    """
    rec_time = time.time() - (req.lag_days_simulated * 86400.0)

    obs, rec_result = state.reconciler.ingest_observation(
        battery_id=req.battery_id,
        cycle_number=req.cycle_number,
        soh_pct=req.soh_pct,
        voltage_v=req.voltage_v,
        temperature_c=req.temperature_c,
        recorded_at=rec_time,
        is_late_explicit=True
    )

    if rec_result is None:
        raise HTTPException(status_code=500, detail="Reconciliation computation failed.")

    return rec_result
