"""
Data models for EvidenceMesh verification engine.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ClaimType(str, Enum):
    ATOMIC_FACT = "atomic_fact"
    STATISTICAL = "statistical"
    CAUSAL_LINK = "causal_link"
    PREDICTION = "prediction"
    NORMATIVE = "normative"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    CONTRADICTED = "CONTRADICTED"
    UNCERTAIN = "UNCERTAIN"
    UNVERIFIABLE = "UNVERIFIABLE"


class EvidenceSource(BaseModel):
    source_id: str
    title: str
    doi_or_url: Optional[str] = None
    domain: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    snippet: str
    reliability_weight: float = Field(default=0.9, ge=0.0, le=1.0)


class AtomicClaim(BaseModel):
    claim_id: str
    text: str
    claim_type: ClaimType = ClaimType.ATOMIC_FACT
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object_value: Optional[str] = None
    numerical_value: Optional[float] = None
    unit: Optional[str] = None
    condition: Optional[str] = None
    status: VerificationStatus = VerificationStatus.UNCERTAIN
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    epistemic_uncertainty: float = Field(default=0.5, ge=0.0, le=1.0)
    aleatoric_uncertainty: float = Field(default=0.1, ge=0.0, le=1.0)
    supporting_evidence: List[EvidenceSource] = Field(default_factory=list)
    refuting_evidence: List[EvidenceSource] = Field(default_factory=list)
    explanation: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)


class CausalEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str  # "entails", "prerequisite_of", "contradicts", "causes"
    weight: float = 1.0


class BayesianCalibrationResult(BaseModel):
    prior_alpha: float
    prior_beta: float
    posterior_alpha: float
    posterior_beta: float
    calibrated_probability: float
    credible_interval_low_95: float
    credible_interval_high_95: float
    expected_calibration_error: float
    brier_score: float
    epistemic_entropy: float


class ProofCertificate(BaseModel):
    certificate_id: str
    claim_root_hash: str
    merkle_root: str
    claim_count: int
    verified_count: int
    contradiction_count: int
    overall_confidence: float
    epistemic_risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    domain: str
    issuer: str = "EvidenceMesh-Autonomous-Proof-Engine-v1"
    leaf_hashes: List[str] = Field(default_factory=list)
    audit_signature: str
    is_tamper_evident_valid: bool = True


class VerificationRequest(BaseModel):
    text_content: str
    domain: Optional[str] = "general"
    prior_skepticism: float = Field(default=0.5, ge=0.0, le=1.0)
    deep_cross_examination: bool = True


class VerificationResponse(BaseModel):
    session_id: str
    original_text: str
    overall_status: VerificationStatus
    calibrated_confidence: float
    epistemic_risk: str
    atomic_claims: List[AtomicClaim]
    causal_edges: List[CausalEdge]
    calibration_metrics: BayesianCalibrationResult
    proof_certificate: ProofCertificate
    audit_trace: List[Dict[str, Any]]
    execution_time_ms: float


class Scenario(BaseModel):
    id: str
    title: str
    category: str
    description: str
    sample_text: str
    ground_truth_context: str
