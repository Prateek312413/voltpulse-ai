"""
Centralized Live System State and Engine Singletons for VoltPulse AI.
"""

from typing import Optional
from ..hardware.can_bus_emulator import CANBusEmulator
from ..hardware.protocols import BatteryChemistry
from .battery_physics import RandlesEISModel, TheveninECM
from .gpr_forecaster import GaussianProcessForecaster
from .thermal_runaway_detector import ThermalRunawayDetector
from .reconciler import TelemetryReconciler
from .active_balancer import ActiveCellBalancer


class SystemState:
    """Singleton holding initialized engines and emulators."""
    _instance: Optional['SystemState'] = None

    def __init__(self):
        self.emulator = CANBusEmulator(pack_id="BESS-GRID-PACK-01", chemistry=BatteryChemistry.NMC_811)
        self.thevenin = TheveninECM()
        self.eis_model = RandlesEISModel()
        self.forecaster = GaussianProcessForecaster()
        self.thermal_detector = ThermalRunawayDetector()
        self.balancer = ActiveCellBalancer()
        self.reconciler = TelemetryReconciler(forecaster=self.forecaster)

        # Seed initial 30 cycles of baseline data
        self.reconciler.seed_initial_telemetry(battery_id="BESS-GRID-PACK-01", count=30)

    @classmethod
    def get_instance(cls) -> 'SystemState':
        if cls._instance is None:
            cls._instance = SystemState()
        return cls._instance


state = SystemState.get_instance()
