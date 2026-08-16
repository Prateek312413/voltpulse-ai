"""
FastAPI Main Application Entrypoint for Uncertainty-Aware Battery Health Forecast Engine.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import settings
from app.database import init_db
from app.api import (
    batteries_router,
    telemetry_router,
    models_router,
    forecasts_router,
    reconciliation_router,
    scenarios_router
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "Uncertainty-Aware Battery Health Forecast Engine with Late-Telemetry Reconciliation. "
        "Built with explicit Cholesky Gaussian Process Regression, bounded numerical jitter ladders, "
        "and non-destructive forecast versioning."
    )
)

# Enable CORS for local development and browser tooling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
def on_startup():
    init_db()

# Mount API routers
app.include_router(batteries_router)
app.include_router(telemetry_router)
app.include_router(models_router)
app.include_router(forecasts_router)
app.include_router(reconciliation_router)
app.include_router(scenarios_router)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the main interactive dashboard UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "HEALTHY", "version": settings.VERSION}
