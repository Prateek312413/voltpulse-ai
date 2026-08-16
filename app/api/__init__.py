"""
FastAPI Routes Package.
"""

from app.api.batteries import router as batteries_router
from app.api.telemetry import router as telemetry_router
from app.api.models import router as models_router
from app.api.forecasts import router as forecasts_router
from app.api.reconciliation import router as reconciliation_router
from app.api.scenarios import router as scenarios_router
