"""
Data Models and Schemas for BioVeil ZK — Midnight Network Protocol
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TrialStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ENROLLMENT_CLOSED = "ENROLLMENT_CLOSED"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"


class AuditScopeEnum(str, Enum):
    FULL_COHORT_SUMMARY = "FULL_COHORT_SUMMARY"
    ADVERSE_EVENT_CONFIRMATION = "ADVERSE_EVENT_CONFIRMATION"
    DEMOGRAPHIC_DISTRIBUTION_PROOF = "DEMOGRAPHIC_DISTRIBUTION_PROOF"
    PROTOCOL_INTEGRITY_AUDIT = "PROTOCOL_INTEGRITY_AUDIT"


class EligibilityCriteriaModel(BaseModel):
    min_age: int = Field(..., ge=0, le=120, description="Minimum eligible age in years")
    max_age: int = Field(..., ge=0, le=120, description="Maximum eligible age in years")
    required_biomarker: str = Field(..., description="Target genomic marker code, e.g., 'HER2_POS_EXON20'")
    required_biomarker_hash: str = Field(..., description="Poseidon/BLAKE2b hash of target biomarker")
    min_egfr_level: int = Field(default=60, ge=0, description="Minimum eGFR level (mL/min/1.73m2)")
    max_blood_pressure_systolic: int = Field(default=140, ge=80, le=240, description="Max systolic BP mmHg")
    excluded_conditions: List[str] = Field(default_factory=list, description="List of excluded comorbidities")
    excluded_conditions_mask: int = Field(default=0, description="Bitmask of excluded medical conditions")


class ClinicalTrialModel(BaseModel):
    trial_id: str = Field(..., description="Unique 32-byte hex ID of the clinical trial")
    title: str = Field(..., description="Human-readable title of trial")
    sponsor_name: str = Field(..., description="Pharma or research institution")
    sponsor_address: str = Field(..., description="Midnight wallet address of sponsor")
    phase: str = Field(default="Phase IIb", description="Clinical trial phase")
    therapeutic_area: str = Field(..., description="e.g. Oncology, Rare Diseases, Neurology")
    description: str = Field(..., description="Detailed description of study objectives")
    criteria: EligibilityCriteriaModel
    status: TrialStatusEnum = Field(default=TrialStatusEnum.ACTIVE)
    max_participants: int = Field(..., gt=0)
    enrolled_count: int = Field(default=0)
    escrow_deposit_night: int = Field(..., description="Total locked NIGHT tokens in escrow")
    milestone_reward_night: int = Field(..., description="NIGHT tokens paid per completed patient milestone")
    creation_timestamp: int
    contract_address: str = Field(default="midnight1q_bioveil_zk_c4109fa8")


class PatientEHRProfile(BaseModel):
    patient_id: str
    full_name: str
    age: int
    gender: str
    biomarkers: List[str]
    egfr_level: int
    systolic_bp: int
    diastolic_bp: int
    diagnosed_conditions: List[str]
    secret_key_hex: str
    midnight_shielded_address: str


class ZKProofGenerationRequest(BaseModel):
    trial_id: str
    patient_profile: PatientEHRProfile
    include_viewing_key: bool = True


class ZKProofCircuitConstraint(BaseModel):
    name: str
    description: str
    circuit_expression: str
    evaluated_truth: bool
    private_value_blinded: str
    public_threshold: str


class ZKProofData(BaseModel):
    proof_id: str
    trial_id: str
    nullifier_hash: str
    public_commitment: str
    proof_bytes_hex: str
    circuit_constraints: List[ZKProofCircuitConstraint]
    proving_time_ms: float
    verification_status: bool
    viewing_key_grant_hash: Optional[str] = None
    created_at_block: int


class ZKProofSubmissionRequest(BaseModel):
    trial_id: str
    nullifier_hash: str
    public_commitment: str
    proof_bytes_hex: str
    shielded_address: str


class MilestoneClaimRequest(BaseModel):
    nullifier_hash: str
    checkpoint_id: str
    completion_secret_hex: str
    shielded_recipient_address: str


class MilestoneClaimResponse(BaseModel):
    success: bool
    transaction_hash: str
    disbursed_amount_night: int
    recipient_address: str
    block_height: int
    message: str


class AuditGrantRequest(BaseModel):
    trial_id: str
    auditor_address: str
    organization_name: str
    jurisdiction_code: int
    scope: AuditScopeEnum
    duration_seconds: int = 86400 * 30


class AuditorVerificationResponse(BaseModel):
    grant_id: str
    trial_id: str
    auditor_address: str
    organization_name: str
    scope: str
    is_valid: bool
    decrypted_cohort_metrics: Dict[str, Any]
    audit_timestamp: int
    verification_log_hash: str


class MidnightTxModel(BaseModel):
    tx_hash: str
    block_height: int
    sender: str
    contract_target: str
    circuit_invoked: str
    shielded_inputs_count: int
    public_disclosures: List[str]
    dust_fee_consumed: int
    timestamp: int
    status: str = "CONFIRMED"


class MidnightBlockModel(BaseModel):
    block_height: int
    block_hash: str
    previous_block_hash: str
    merkle_root: str
    timestamp: int
    transactions_count: int
    transactions: List[MidnightTxModel]
    prover_node_id: str


class MidnightNetworkStats(BaseModel):
    network_name: str = "Midnight Preview Testnet (4101)"
    current_block_height: int
    total_shielded_proofs: int
    active_compact_contracts: int
    total_locked_night_escrow: int
    total_disbursed_night: int
    current_dust_rate: float
    prover_network_health: str = "100% HEALTHY (Zero Knowledge Halo2 Engine)"
