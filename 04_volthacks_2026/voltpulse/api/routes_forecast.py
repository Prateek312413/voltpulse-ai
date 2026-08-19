"""
API Routes for GPR SOH/RUL Predictions, Kernel Benchmarking, and Uncertainty Bounds.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from ..core.state import state
from ..core.gpr_forecaster import GPRKernelType, ForecastResult, ModelEvaluationResult

router = APIRouter(prefix="/api/forecast", tags=["GPR Forecasting"])


class ForecastRequest(BaseModel):
    battery_id: str = "BESS-GRID-PACK-01"
    horizon_cycles: int = 150
    preferred_kernel: Optional[GPRKernelType] = None


@router.get("/latest", response_model=ForecastResult)
def get_latest_forecast(battery_id: str = "BESS-GRID-PACK-01"):
    """
    Retrieve the latest active Gaussian Process SOH forecast with 95% confidence intervals.
    """
    if battery_id not in state.reconciler.active_forecasts:
        # Fallback generate
        state.reconciler.seed_initial_telemetry(battery_id=battery_id, count=30)

    return state.reconciler.active_forecasts[battery_id]


@router.get("/kernel_benchmark", response_model=List[ModelEvaluationResult])
def benchmark_kernels(battery_id: str = "BESS-GRID-PACK-01"):
    """
    Run deterministic multi-kernel validation comparison across Matérn 5/2, Matérn 3/2,
    RBF, Rational Quadratic, and ARD Composite kernels.
    """
    observations = state.reconciler.observations.get(battery_id, [])
    if not observations:
        state.reconciler.seed_initial_telemetry(battery_id=battery_id, count=30)
        observations = state.reconciler.observations.get(battery_id, [])

    cycles = [r.cycle_number for r in observations]
    sohs = [r.soh_pct for r in observations]

    evaluations = state.forecaster.evaluate_candidate_kernels(cycles, sohs)
    return evaluations


@router.post("/generate", response_model=ForecastResult)
def generate_custom_forecast(req: ForecastRequest):
    """
    Generate a custom forward-looking forecast with explicit horizon or kernel override.
    """
    observations = state.reconciler.observations.get(req.battery_id, [])
    if not observations:
        state.reconciler.seed_initial_telemetry(battery_id=req.battery_id, count=30)
        observations = state.reconciler.observations.get(req.battery_id, [])

    cycles = [r.cycle_number for r in observations]
    sohs = [r.soh_pct for r in observations]

    res = state.forecaster.forecast(
        battery_id=req.battery_id,
        cycles=cycles,
        sohs=sohs,
        forecast_horizon_cycles=req.horizon_cycles,
        preferred_kernel=req.preferred_kernel
    )
    state.reconciler.active_forecasts[req.battery_id] = res
    return res
