"""
ResilioNet AI - REST API Routes Package
Built for HackSocial 2026 Hackathon
"""

from fastapi import APIRouter
from .routes_triage import router as triage_router
from .routes_resources import router as resources_router
from .routes_matching import router as matching_router
from .routes_mesh import router as mesh_router
from .routes_analytics import router as analytics_router

api_router = APIRouter()
api_router.include_router(triage_router, prefix="/triage", tags=["Crisis Triage & NLP"])
api_router.include_router(resources_router, prefix="/resources", tags=["Supply Depots & Inventory"])
api_router.include_router(matching_router, prefix="/matching", tags=["Resource Matching & Optimization"])
api_router.include_router(mesh_router, prefix="/mesh", tags=["Offline Mesh Protocol & Ledger"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Situational Awareness & Analytics"])

__all__ = ["api_router"]
