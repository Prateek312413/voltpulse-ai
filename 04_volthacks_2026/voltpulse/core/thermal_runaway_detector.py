"""
Sub-millisecond Early-Warning Thermal Runaway & Separator Micro-Short Anomaly Detector.
"""

from enum import Enum
import time
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field


class ThermalRiskLevel(str, Enum):
    NOMINAL = "NOMINAL"
    ELEVATED = "ELEVATED"
    WARNING = "WARNING"
    CRITICAL_RUNAWAY = "CRITICAL_RUNAWAY"


class CellAnomalyDetail(BaseModel):
    cell_id: int
    current_temp_c: float
    dt_dt_c_per_sec: float
    dv_dt_v_per_sec: float
    temp_divergence_from_mean_c: float
    risk_score: float
    risk_level: ThermalRiskLevel
    micro_short_detected: bool


class ThermalSafetyReport(BaseModel):
    timestamp: float
    overall_risk_level: ThermalRiskLevel
    is_safe: bool
    contactor_trip_recommended: bool
    max_cell_temp_c: float
    max_gradient_c_per_sec: float
    critical_cell_ids: List[int]
    anomalous_cells: List[CellAnomalyDetail]
    detection_latency_ms: float
    diagnostic_message: str


class ThermalRunawayDetector:
    """
    Real-time electrochemical and thermal gradient surveillance engine.
    Monitors 16 cells for simultaneous thermal acceleration and voltage collapse (micro-shorts).
    """

    def __init__(
        self,
        dt_warning_thresh: float = 1.2,      # °C/sec
        dt_critical_thresh: float = 2.8,     # °C/sec
        dv_microshort_thresh: float = -0.025, # V/sec collapse
        max_divergence_thresh: float = 6.0,  # °C from pack mean
        max_absolute_temp_thresh: float = 58.0 # °C
    ):
        self.dt_warning = dt_warning_thresh
        self.dt_critical = dt_critical_thresh
        self.dv_microshort = dv_microshort_thresh
        self.max_divergence = max_divergence_thresh
        self.max_absolute_temp = max_absolute_temp_thresh

        # Historical state tracking per cell for derivatives
        self.prev_time: Optional[float] = None
        self.prev_temps: Dict[int, float] = {}
        self.prev_voltages: Dict[int, float] = {}

    def analyze_frame(
        self,
        timestamp: float,
        cell_data: List[Dict[str, float]]
    ) -> ThermalSafetyReport:
        """
        Analyze current pack telemetry and evaluate thermal runaway safety.
        cell_data format: [{'cell_id': 1, 'voltage_v': 3.75, 'temperature_c': 28.5}, ...]
        """
        t_start = time.perf_counter()

        dt = 0.5  # default baseline
        if self.prev_time is not None:
            dt = max(0.01, timestamp - self.prev_time)

        # Pack mean temperature
        current_temps = [c['temperature_c'] for c in cell_data]
        mean_temp = sum(current_temps) / max(1, len(current_temps))

        anomalies: List[CellAnomalyDetail] = []
        critical_cells: List[int] = []
        max_dt_dt = 0.0
        max_t = max(current_temps) if current_temps else 0.0

        for c in cell_data:
            cid = int(c['cell_id'])
            v_curr = float(c['voltage_v'])
            t_curr = float(c['temperature_c'])

            # Compute derivatives
            t_prev = self.prev_temps.get(cid, t_curr)
            v_prev = self.prev_voltages.get(cid, v_curr)

            dt_dt = (t_curr - t_prev) / dt
            dv_dt = (v_curr - v_prev) / dt

            max_dt_dt = max(max_dt_dt, abs(dt_dt))
            temp_div = t_curr - mean_temp

            # Micro-short detection: simultaneous negative dV/dt and positive dT/dt
            micro_short = (dv_dt <= self.dv_microshort and dt_dt >= 0.8)

            # Compound risk score
            # Score = |dT/dt| * 2.0 + (temp_div) * 1.5 + (10.0 if micro_short else 0) + (15.0 if t_curr > max_absolute_temp else 0)
            score = max(0.0, dt_dt * 2.5 + temp_div * 1.2)
            if micro_short:
                score += 15.0
            if t_curr >= self.max_absolute_temp:
                score += 20.0

            # Determine risk level
            if score >= 12.0 or t_curr >= 65.0 or dt_dt >= self.dt_critical:
                level = ThermalRiskLevel.CRITICAL_RUNAWAY
                critical_cells.append(cid)
            elif score >= 6.0 or t_curr >= 50.0 or dt_dt >= self.dt_warning or temp_div >= self.max_divergence:
                level = ThermalRiskLevel.WARNING
            elif score >= 2.5 or temp_div >= 3.5:
                level = ThermalRiskLevel.ELEVATED
            else:
                level = ThermalRiskLevel.NOMINAL

            anomalies.append(CellAnomalyDetail(
                cell_id=cid,
                current_temp_c=round(t_curr, 2),
                dt_dt_c_per_sec=round(dt_dt, 3),
                dv_dt_v_per_sec=round(dv_dt, 4),
                temp_divergence_from_mean_c=round(temp_div, 2),
                risk_score=round(score, 2),
                risk_level=level,
                micro_short_detected=micro_short
            ))

            # Update cache
            self.prev_temps[cid] = t_curr
            self.prev_voltages[cid] = v_curr

        self.prev_time = timestamp

        # Determine overall pack risk
        if critical_cells:
            overall_risk = ThermalRiskLevel.CRITICAL_RUNAWAY
            trip_recommended = True
            is_safe = False
            msg = f"CRITICAL: Thermal runaway initiated on Cell(s) {critical_cells}! dT/dt={max_dt_dt:.2f}°C/s. Immediate contactor isolation required."
        elif any(a.risk_level == ThermalRiskLevel.WARNING for a in anomalies):
            overall_risk = ThermalRiskLevel.WARNING
            trip_recommended = False
            is_safe = True
            msg = "WARNING: Elevated thermal divergence and localized heating detected. Derating discharge power."
        elif any(a.risk_level == ThermalRiskLevel.ELEVATED for a in anomalies):
            overall_risk = ThermalRiskLevel.ELEVATED
            trip_recommended = False
            is_safe = True
            msg = "ELEVATED: Minor temperature imbalance detected across series string."
        else:
            overall_risk = ThermalRiskLevel.NOMINAL
            trip_recommended = False
            is_safe = True
            msg = "NOMINAL: All 16 cells operating within normal thermal and electrochemical envelopes."

        t_end = time.perf_counter()
        latency_ms = round((t_end - t_start) * 1000.0, 3)

        return ThermalSafetyReport(
            timestamp=timestamp,
            overall_risk_level=overall_risk,
            is_safe=is_safe,
            contactor_trip_recommended=trip_recommended,
            max_cell_temp_c=round(max_t, 2),
            max_gradient_c_per_sec=round(max_dt_dt, 3),
            critical_cell_ids=critical_cells,
            anomalous_cells=anomalies,
            detection_latency_ms=latency_ms,
            diagnostic_message=msg
        )
