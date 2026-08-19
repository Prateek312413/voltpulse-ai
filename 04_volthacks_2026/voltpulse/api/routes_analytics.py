"""
API Routes for Nyquist EIS Spectrum, SEI Degradation Physics, and SCADA Operations KPIs.
"""

from fastapi import APIRouter
from typing import List, Dict, Any

from ..core.state import state
from ..core.battery_physics import calculate_sei_growth, EISDataPoint

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Physics"])


@router.get("/nyquist_spectrum", response_model=List[EISDataPoint])
def get_nyquist_eis_spectrum(soh_pct: float = 94.2, temp_c: float = 28.0):
    """
    Generate real-time Electrochemical Impedance Spectroscopy (EIS) Nyquist spectrum
    spanning 10 kHz down to 10 mHz for impedance arc and Warburg diffusion analysis.
    """
    return state.eis_model.compute_nyquist_spectrum(soh_pct=soh_pct, temp_c=temp_c, num_points=45)


@router.get("/sei_degradation")
def get_sei_growth_curve(cycles: int = 500, avg_temp_c: float = 32.0, c_rate: float = 1.0):
    """
    Calculate physics-based Solid Electrolyte Interphase (SEI) growth curve over cycle life.
    """
    points = []
    for c in range(10, cycles + 10, 20):
        res = calculate_sei_growth(cycles=c, avg_temp_c=avg_temp_c, c_rate=c_rate)
        points.append({
            "cycle": c,
            "soh_pct": res["soh_pct"],
            "capacity_loss_pct": res["capacity_loss_pct"],
            "sei_thickness_nm": res["sei_thickness_nm"],
            "resistance_increase_pct": res["resistance_increase_pct"]
        })
    return {
        "current_cycles": cycles,
        "parameters": {"avg_temp_c": avg_temp_c, "c_rate": c_rate},
        "growth_curve": points
    }


@router.get("/summary_kpis")
def get_summary_kpis():
    """
    Top-level telemetry and status summary for SCADA Operations command center.
    """
    frame = state.emulator.step(dt=0.1)

    # Convert cells to format for thermal detector
    cells_raw = [
        {"cell_id": c.cell_id, "voltage_v": c.voltage_v, "temperature_c": c.temperature_c}
        for c in frame.cells
    ]
    safety_report = state.thermal_detector.analyze_frame(timestamp=frame.timestamp, cell_data=cells_raw)
    forecast = state.reconciler.active_forecasts.get(frame.pack_id)

    return {
        "pack_id": frame.pack_id,
        "chemistry": frame.chemistry.value,
        "pack_voltage_v": frame.pack_voltage_v,
        "pack_current_a": frame.pack_current_a,
        "pack_power_kw": frame.pack_power_kw,
        "pack_soc_pct": frame.pack_soc_pct,
        "pack_soh_pct": frame.pack_soh_pct,
        "rul_cycles": forecast.remaining_useful_life_cycles if forecast else None,
        "selected_gpr_kernel": forecast.selected_kernel.value if forecast else "MATERN_52",
        "contactor_status": frame.contactor_status.value,
        "thermal_risk_level": safety_report.overall_risk_level.value,
        "max_cell_temp_c": frame.max_cell_temp_c,
        "min_cell_temp_c": frame.min_cell_temp_c,
        "cell_voltage_delta_mv": frame.cell_voltage_delta_mv,
        "balancing_status": frame.balancing_status.value,
        "telemetry_version": state.reconciler.telemetry_versions.get(frame.pack_id, 1),
        "reconciliation_events_count": len(state.reconciler.reconciliation_history),
        "safety_message": safety_report.diagnostic_message
    }
