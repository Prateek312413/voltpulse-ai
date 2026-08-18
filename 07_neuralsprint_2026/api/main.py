"""
FastAPI Entrypoint for NeuroAccess AI Server
"""
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from .routes import router

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="NeuroAccess AI Engine",
    description="Assistive Neuro-Adaptive Communication & Multi-Modal AAC Platform for NeuralSprint 2026",
    version="1.0.0"
)

# CORS middleware for open accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
static_dir = BASE_DIR / "web" / "static"
templates_dir = BASE_DIR / "web" / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))

# Include API routes
app.include_router(router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Silently handles browser favicon requests."""
    return Response(status_code=204)

@app.get("/")
async def serve_index(request: Request):
    """Serves the main accessible AAC & speech restoration dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "NeuroAccess AI - Assistive AAC & Speech Engine"}
    )
