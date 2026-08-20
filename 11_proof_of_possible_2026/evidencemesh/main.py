"""
EvidenceMesh Main Application Entrypoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from evidencemesh.config import settings
from evidencemesh.api.routes import router as api_router
from evidencemesh.api.websocket import ws_router
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[*] Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"[*] {settings.TAGLINE}")
    print(f"[*] Server available at: http://{settings.HOST}:{settings.PORT}")
    yield
    print(f"[*] Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.TAGLINE,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include Routers
app.include_router(api_router, prefix="/api", tags=["Verification API"])
app.include_router(ws_router, tags=["WebSocket Streaming"])

# Mount static directory for frontend console
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
