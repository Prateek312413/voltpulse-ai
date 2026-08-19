"""
REST API Routers for VoltPulse AI Platform.
"""

from .routes_telemetry import router as telemetry_router
from .routes_forecast import router as forecast_router
from .routes_reconciliation import router as reconciliation_router
from .routes_hardware import router as hardware_router
from .routes_analytics import router as analytics_router

__all__ = [
    "telemetry_router",
    "forecast_router",
    "reconciliation_router",
    "hardware_router",
    "analytics_router",
]
