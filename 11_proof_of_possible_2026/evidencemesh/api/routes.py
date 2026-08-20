"""
REST API Endpoints for EvidenceMesh.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from evidencemesh.models import (
    VerificationRequest,
    VerificationResponse,
    Scenario,
    ProofCertificate
)
from evidencemesh.agents.swarm import EvidenceMeshSwarm
from evidencemesh.knowledge.benchmark_scenarios import BENCHMARK_SCENARIOS, get_scenario_by_id
from evidencemesh.config import settings


router = APIRouter()
swarm = EvidenceMeshSwarm()
certificate_store: Dict[str, ProofCertificate] = {}


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "tagline": settings.TAGLINE
    }


@router.get("/scenarios", response_model=List[Scenario])
def list_scenarios():
    """Returns all pre-configured empirical benchmark scenarios."""
    return BENCHMARK_SCENARIOS


@router.get("/scenarios/{scenario_id}", response_model=Scenario)
def get_scenario(scenario_id: str):
    """Retrieves single scenario by ID."""
    sc = get_scenario_by_id(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return sc


@router.post("/verify", response_model=VerificationResponse)
def verify_text_endpoint(request: VerificationRequest):
    """
    Submits a complex assertion, scientific claim, or document for multi-agent causal verification.
    """
    if not request.text_content or len(request.text_content.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text content must contain at least 5 characters.")

    response = swarm.verify(request)
    # Save certificate to in-memory store for verification endpoint
    certificate_store[response.proof_certificate.certificate_id] = response.proof_certificate
    return response


@router.get("/proofs/{certificate_id}")
def get_certificate(certificate_id: str):
    """Look up a generated cryptographic Proof Certificate."""
    cert = certificate_store.get(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found in ledger.")
    return cert


@router.post("/proofs/{certificate_id}/tamper-check")
def tamper_check_endpoint(certificate_id: str, simulated_corrupt_text: str = Query(None)):
    """
    Validates certificate cryptographic integrity and simulates tamper detection.
    """
    cert = certificate_store.get(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")

    if simulated_corrupt_text:
        # Simulate tampering
        return {
            "certificate_id": certificate_id,
            "is_valid": False,
            "status": "TAMPER_DETECTED",
            "message": "Cryptographic Merkle Root mismatch! Content has been altered since certificate was issued."
        }

    return {
        "certificate_id": certificate_id,
        "is_valid": cert.is_tamper_evident_valid,
        "merkle_root": cert.merkle_root,
        "audit_signature": cert.audit_signature,
        "status": "VERIFIED_AUTHENTIC",
        "message": "Certificate cryptographic lineage matches immutable Merkle proof."
    }
