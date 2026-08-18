"""
ResilioNet AI - Main FastAPI Application Server
Built for HackSocial 2026 Hackathon (Devpost)
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
try:
    from api import api_router
except ImportError:
    from .api import api_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

app = FastAPI(
    title="ResilioNet AI",
    description="Autonomous Multi-Modal Disaster Resilience, Resource Allocation & Hyperlocal Mutual-Aid Coordination Network",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin or local embedded tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

# Serve Web Static Files
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "ResilioNet AI API Online",
        "docs": "/docs",
        "health": "OK"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "engine": "ResilioNet AI",
        "edition": "HackSocial 2026",
        "version": "1.0.0"
    }
