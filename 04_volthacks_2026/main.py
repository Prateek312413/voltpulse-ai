"""
VoltPulse AI: FastAPI Application Gateway & Microservices Orchestrator.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
import os

from voltpulse.api import (
    telemetry_router,
    forecast_router,
    reconciliation_router,
    hardware_router,
    analytics_router,
)

app = FastAPI(
    title="VoltPulse AI",
    description="Edge-AI Battery Management & Grid-Scale Thermal-Electrochemical Resilience Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(telemetry_router)
app.include_router(forecast_router)
app.include_router(reconciliation_router)
app.include_router(hardware_router)
app.include_router(analytics_router)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "voltpulse", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve interactive SCADA Digital Twin Dashboard."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "VoltPulse AI API Gateway Online", "docs": "/docs"}


@app.get("/api/health")
def health_check():
    """System health check and engine readiness telemetry."""
    return {
        "status": "HEALTHY",
        "service": "VoltPulse AI Edge Engine",
        "version": "1.0.0",
        "protocols": ["SAE J1939 CAN-bus", "Modbus TCP", "FastAPI REST"]
    }
