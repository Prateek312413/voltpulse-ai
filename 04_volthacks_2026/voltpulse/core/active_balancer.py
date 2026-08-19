"""
Cell Balancing Algorithms (Passive Bleed, Active Charge Shuttling) and Contactor Safety Interlocks.
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel

from ..hardware.protocols import BalancingState, ContactorState, CellTelemetry


class BalancingDecision(BaseModel):
    balancing_state: BalancingState
    target_cells_to_balance: List[int]
    max_voltage_v: float
    min_voltage_v: float
    delta_mv: float
    is_balancing_needed: bool
    estimated_balance_time_mins: float
    contactor_interlock_trip: bool
    safety_fault_reason: Optional[str] = None


class ActiveCellBalancer:
    """
    Evaluates cell state-of-charge divergence and schedules balancing pulses.
    """

    def __init__(
        self,
        balance_threshold_mv: float = 12.0,       # Start balancing if delta > 12mV
        critical_delta_mv: float = 180.0,         # Trip contactor if delta > 180mV
        cell_over_voltage_limit_v: float = 4.25,   # Trip if V > 4.25V
        cell_under_voltage_limit_v: float = 2.70   # Trip if V < 2.70V
    ):
        self.balance_threshold_mv = balance_threshold_mv
        self.critical_delta_mv = critical_delta_mv
        self.ov_limit = cell_over_voltage_limit_v
        self.uv_limit = cell_under_voltage_limit_v

    def evaluate_pack(self, cells: List[CellTelemetry]) -> BalancingDecision:
        """
        Analyze cell voltages and compute balancing commands.
        """
        voltages = [c.voltage_v for c in cells]
        max_v = max(voltages)
        min_v = min(voltages)
        mean_v = sum(voltages) / max(1, len(voltages))
        delta_mv = (max_v - min_v) * 1000.0

        # Safety Checks
        fault_reason = None
        trip_contactor = False

        if max_v >= self.ov_limit:
            trip_contactor = True
            fault_reason = f"CRITICAL_CELL_OVERVOLTAGE: Max cell voltage {max_v:.3f}V exceeds safety ceiling {self.ov_limit:.2f}V"
        elif min_v <= self.uv_limit:
            trip_contactor = True
            fault_reason = f"CRITICAL_CELL_UNDERVOLTAGE: Min cell voltage {min_v:.3f}V below safety floor {self.uv_limit:.2f}V"
        elif delta_mv >= self.critical_delta_mv:
            trip_contactor = True
            fault_reason = f"CRITICAL_CELL_IMBALANCE: Voltage spread {delta_mv:.1f}mV exceeds critical limit {self.critical_delta_mv:.1f}mV"

        # Balancing logic: target cells above mean + threshold
        target_cells = []
        if delta_mv >= self.balance_threshold_mv:
            for c in cells:
                if (c.voltage_v - mean_v) * 1000.0 >= (self.balance_threshold_mv / 2.0):
                    target_cells.append(c.cell_id)

        balancing_state = BalancingState.ACTIVE_BLEEDING if target_cells else BalancingState.IDLE
        # 100mA bleed current on 100Ah cell: estimate time
        excess_mv = max(0.0, delta_mv - self.balance_threshold_mv)
        est_mins = round((excess_mv / 1000.0) * 100.0 * 2.5, 1) if target_cells else 0.0

        return BalancingDecision(
            balancing_state=balancing_state,
            target_cells_to_balance=target_cells,
            max_voltage_v=round(max_v, 4),
            min_voltage_v=round(min_v, 4),
            delta_mv=round(delta_mv, 1),
            is_balancing_needed=len(target_cells) > 0,
            estimated_balance_time_mins=est_mins,
            contactor_interlock_trip=trip_contactor,
            safety_fault_reason=fault_reason
        )
