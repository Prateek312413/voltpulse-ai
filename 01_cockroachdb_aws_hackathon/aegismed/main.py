"""
AegisMed Application Entrypoint
Initializes FastAPI, mounts static clinician console, and sets up lifecycle hooks.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from aegismed.config import settings
from aegismed.database.connection import init_db, active_backend
from aegismed.database.seed_data import seed_all
from aegismed.api.routes import router as api_router

logger = logging.getLogger("aegismed.main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Resilient Clinical Agentic Memory Engine built for the CockroachDB × AWS Hackathon."
)

# Enable CORS for local development and web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount Static Files (Clinician Dashboard)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.on_event("startup")
def on_startup():
    """Startup initialization: initialize tables & seed benchmark data."""
    logger.info("Initializing AegisMed Agentic Memory Engine...")
    init_db()
    seed_all()
    logger.info(f"AegisMed Engine is ready on http://{settings.HOST}:{settings.PORT} [Backend: {active_backend}]")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("aegismed.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
