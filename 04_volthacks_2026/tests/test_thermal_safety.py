"""
Unit tests for Early Thermal Runaway Detection, Micro-Short Classification, and Contactor Interlocks.
"""

import pytest
from voltpulse.core.thermal_runaway_detector import (
    ThermalRunawayDetector,
    ThermalRiskLevel,
)
from voltpulse.core.active_balancer import ActiveCellBalancer
from voltpulse.hardware.protocols import CellTelemetry


def test_thermal_runaway_nominal_baseline():
    detector = ThermalRunawayDetector()
    cell_data = [
        {"cell_id": i, "voltage_v": 3.75, "temperature_c": 28.0}
        for i in range(1, 17)
    ]

    report = detector.analyze_frame(timestamp=100.0, cell_data=cell_data)
    assert report.is_safe is True
    assert report.contactor_trip_recommended is False
    assert report.overall_risk_level == ThermalRiskLevel.NOMINAL
    assert report.detection_latency_ms < 5.0


def test_thermal_runaway_critical_trip():
    detector = ThermalRunawayDetector()
    # Step 1: Baseline
    cell_data_1 = [
        {"cell_id": i, "voltage_v": 3.75, "temperature_c": 28.0}
        for i in range(1, 17)
    ]
    detector.analyze_frame(timestamp=100.0, cell_data=cell_data_1)

    # Step 2: Cell 7 runaway: temp leaps by +5C in 0.5s (10C/s), voltage drops by -0.15V
    cell_data_2 = [
        {"cell_id": i, "voltage_v": 3.75, "temperature_c": 28.1}
        for i in range(1, 17)
    ]
    cell_data_2[6] = {"cell_id": 7, "voltage_v": 3.60, "temperature_c": 33.1}

    report = detector.analyze_frame(timestamp=100.5, cell_data=cell_data_2)
    assert report.contactor_trip_recommended is True
    assert report.overall_risk_level == ThermalRiskLevel.CRITICAL_RUNAWAY
    assert 7 in report.critical_cell_ids


def test_active_cell_balancer_interlocks():
    balancer = ActiveCellBalancer(balance_threshold_mv=12.0, critical_delta_mv=180.0)

    # Normal pack with small 15mV spread
    cells_normal = [
        CellTelemetry(cell_id=i, voltage_v=3.750 + (0.015 if i == 3 else 0.0), temperature_c=28.0, soc_pct=85.0, internal_resistance_mohm=1.2)
        for i in range(1, 17)
    ]
    decision = balancer.evaluate_pack(cells_normal)
    assert decision.is_balancing_needed is True
    assert 3 in decision.target_cells_to_balance
    assert decision.contactor_interlock_trip is False

    # Extreme critical imbalance
    cells_fault = [
        CellTelemetry(cell_id=i, voltage_v=3.750 if i != 1 else 3.500, temperature_c=28.0, soc_pct=85.0, internal_resistance_mohm=1.2)
        for i in range(1, 17)
    ]
    decision_fault = balancer.evaluate_pack(cells_fault)
    assert decision_fault.contactor_interlock_trip is True
