"""
Deterministic Late-Telemetry & Out-of-Order IoT Sensor Reconciliation Engine.
"""

from typing import List, Dict, Tuple, Optional, Any
import time
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from .gpr_forecaster import GaussianProcessForecaster, ForecastResult, GPRKernelType


class ObservationRecord(BaseModel):
    observation_id: str
    battery_id: str
    cycle_number: float
    recorded_at: float
    received_at: float
    soh_pct: float
    voltage_v: float
    temperature_c: float
    is_late: bool = False
    is_corrected: bool = False
    replaces_observation_id: Optional[str] = None


class ReconciliationDiff(BaseModel):
    previous_soh_prediction: float
    reconciled_soh_prediction: float
    soh_prediction_delta: float
    previous_uncertainty_std: float
    reconciled_uncertainty_std: float
    uncertainty_delta: float
    previous_selected_kernel: str
    reconciled_selected_kernel: str
    kernel_changed: bool
    previous_rul_cycles: Optional[float]
    reconciled_rul_cycles: Optional[float]
    rul_delta_cycles: Optional[float]


class ReconciliationResult(BaseModel):
    reconciliation_id: str
    battery_id: str
    timestamp: float
    telemetry_version: int
    late_observations_ingested: int
    total_active_observations: int
    reconciliation_duration_ms: float
    diff: ReconciliationDiff
    new_forecast: ForecastResult


class TelemetryReconciler:
    """
    Manages versioned observation storage and deterministic timeline reconstruction.
    """

    def __init__(self, forecaster: Optional[GaussianProcessForecaster] = None):
        self.forecaster = forecaster or GaussianProcessForecaster()
        self.observations: Dict[str, List[ObservationRecord]] = {}
        self.active_forecasts: Dict[str, ForecastResult] = {}
        self.telemetry_versions: Dict[str, int] = {}
        self.reconciliation_history: List[ReconciliationResult] = []

    def seed_initial_telemetry(self, battery_id: str, count: int = 30):
        """Seed a clean baseline of 30 historical cycles for a battery."""
        records = []
        base_time = time.time() - (count * 86400.0)
        self.telemetry_versions[battery_id] = 1

        for i in range(count):
            cycle = float(i * 10 + 10)
            # True degradation curve + small noise
            true_soh = 100.0 - 0.045 * cycle - 0.00003 * (cycle ** 2)
            rec_time = base_time + (i * 86400.0)
            records.append(ObservationRecord(
                observation_id=f"OBS-{battery_id}-CYC{int(cycle)}",
                battery_id=battery_id,
                cycle_number=cycle,
                recorded_at=rec_time,
                received_at=rec_time + 1.2,
                soh_pct=round(true_soh, 2),
                voltage_v=round(3.72 - 0.001 * cycle, 3),
                temperature_c=round(28.0 + (i % 5) * 0.4, 1),
                is_late=False
            ))

        self.observations[battery_id] = records
        # Fit baseline forecast
        cycles = [r.cycle_number for r in records]
        sohs = [r.soh_pct for r in records]
        self.active_forecasts[battery_id] = self.forecaster.forecast(battery_id, cycles, sohs)

    def ingest_observation(
        self,
        battery_id: str,
        cycle_number: float,
        soh_pct: float,
        voltage_v: float,
        temperature_c: float,
        recorded_at: Optional[float] = None,
        is_late_explicit: bool = False
    ) -> Tuple[ObservationRecord, Optional[ReconciliationResult]]:
        """
        Ingest a new observation. Automatically detects out-of-order/late records and reconciles.
        """
        t_start = time.perf_counter()
        now = time.time()
        rec_at = recorded_at if recorded_at is not None else now

        if battery_id not in self.observations:
            self.observations[battery_id] = []
            self.telemetry_versions[battery_id] = 0

        existing = self.observations[battery_id]
        # Check if late
        max_existing_cycle = max([r.cycle_number for r in existing]) if existing else 0.0
        is_late = is_late_explicit or (cycle_number < max_existing_cycle)

        obs = ObservationRecord(
            observation_id=f"OBS-{battery_id}-{int(now*1000)%1000000}",
            battery_id=battery_id,
            cycle_number=cycle_number,
            recorded_at=rec_at,
            received_at=now,
            soh_pct=soh_pct,
            voltage_v=voltage_v,
            temperature_c=temperature_c,
            is_late=is_late
        )

        existing.append(obs)
        self.telemetry_versions[battery_id] += 1

        # Re-sort timeline deterministically by event cycle / recorded_at
        existing.sort(key=lambda r: (r.cycle_number, r.recorded_at))

        # Re-evaluate forecast
        reconciliation_res = None
        if is_late or battery_id in self.active_forecasts:
            prev_forecast = self.active_forecasts.get(battery_id)
            cycles = [r.cycle_number for r in existing]
            sohs = [r.soh_pct for r in existing]

            new_forecast = self.forecaster.forecast(battery_id, cycles, sohs)
            self.active_forecasts[battery_id] = new_forecast

            t_end = time.perf_counter()
            duration_ms = round((t_end - t_start) * 1000.0, 3)

            # Build diff
            if prev_forecast:
                # Compare forecast at current horizon
                prev_last = prev_forecast.forecast_curve[-1]
                new_last = new_forecast.forecast_curve[-1]

                soh_delta = round(new_last.predicted_soh_pct - prev_last.predicted_soh_pct, 2)
                unc_delta = round(new_last.std_dev - prev_last.std_dev, 3)
                prev_rul = prev_forecast.remaining_useful_life_cycles
                new_rul = new_forecast.remaining_useful_life_cycles
                rul_delta = round(new_rul - prev_rul, 1) if (new_rul and prev_rul) else None

                diff = ReconciliationDiff(
                    previous_soh_prediction=prev_last.predicted_soh_pct,
                    reconciled_soh_prediction=new_last.predicted_soh_pct,
                    soh_prediction_delta=soh_delta,
                    previous_uncertainty_std=prev_last.std_dev,
                    reconciled_uncertainty_std=new_last.std_dev,
                    uncertainty_delta=unc_delta,
                    previous_selected_kernel=prev_forecast.selected_kernel.value,
                    reconciled_selected_kernel=new_forecast.selected_kernel.value,
                    kernel_changed=(prev_forecast.selected_kernel != new_forecast.selected_kernel),
                    previous_rul_cycles=prev_rul,
                    reconciled_rul_cycles=new_rul,
                    rul_delta_cycles=rul_delta
                )
            else:
                diff = ReconciliationDiff(
                    previous_soh_prediction=0.0,
                    reconciled_soh_prediction=new_forecast.forecast_curve[-1].predicted_soh_pct,
                    soh_prediction_delta=0.0,
                    previous_uncertainty_std=0.0,
                    reconciled_uncertainty_std=new_forecast.forecast_curve[-1].std_dev,
                    uncertainty_delta=0.0,
                    previous_selected_kernel="NONE",
                    reconciled_selected_kernel=new_forecast.selected_kernel.value,
                    kernel_changed=False,
                    previous_rul_cycles=None,
                    reconciled_rul_cycles=new_forecast.remaining_useful_life_cycles,
                    rul_delta_cycles=None
                )

            reconciliation_res = ReconciliationResult(
                reconciliation_id=f"REC-{battery_id}-{self.telemetry_versions[battery_id]}",
                battery_id=battery_id,
                timestamp=now,
                telemetry_version=self.telemetry_versions[battery_id],
                late_observations_ingested=sum(1 for r in existing if r.is_late),
                total_active_observations=len(existing),
                reconciliation_duration_ms=duration_ms,
                diff=diff,
                new_forecast=new_forecast
            )
            self.reconciliation_history.append(reconciliation_res)

        return obs, reconciliation_res
