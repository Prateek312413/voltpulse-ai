"""
BioVeil ZK — FastAPI Backend & Real-time Midnight Protocol Gateway
"""

import os
import time
import asyncio
import secrets
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.data_models import (
    ClinicalTrialModel,
    EligibilityCriteriaModel,
    PatientEHRProfile,
    ZKProofGenerationRequest,
    ZKProofData,
    ZKProofSubmissionRequest,
    MilestoneClaimRequest,
    MilestoneClaimResponse,
    AuditGrantRequest,
    AuditorVerificationResponse,
    MidnightNetworkStats,
    MidnightBlockModel
)
from backend.zk_engine import BioVeilZKProver, BioVeilZKVerifier, compute_biomarker_hash, compute_condition_mask
from backend.midnight_client import MidnightNetworkClient
from backend.sample_data import get_sample_patients
from backend.compliance_audit import ComplianceAuditManager
from backend.clinical_agent import (
    ClinicalPharmacovigilanceSentinel,
    BayesianBiomarkerTrajectoryEngine,
    MCDAClinicalTrialMatcher
)

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
CONTRACTS_DIR = BASE_DIR / "contracts"

app = FastAPI(
    title="BioVeil ZK API Gateway",
    description="Zero-Knowledge Clinical Trial & Genomic Intelligence Protocol on Midnight Blockchain",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Protocol Singletons
midnight_client = MidnightNetworkClient()
audit_manager = ComplianceAuditManager()
sample_patients = get_sample_patients()

# WebSocket Connection Manager for Real-time Midnight Block Stream
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()


# Background Task for Synthetic Midnight Block Production
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_block_miner())


async def background_block_miner():
    """Generates continuous block activity mimicking the Midnight Preview testnet."""
    while True:
        try:
            await asyncio.sleep(8)  # 8-second block cadence
            new_block = midnight_client.mine_synthetic_heartbeat_block()
            await ws_manager.broadcast({
                "type": "NEW_MIDNIGHT_BLOCK",
                "block": new_block.model_dump(),
                "network_stats": midnight_client.get_network_stats().model_dump()
            })
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in background miner: {e}")
            await asyncio.sleep(5)


# -----------------------------------------------------------------------------
# REST API Endpoints: Network & Telemetry
# -----------------------------------------------------------------------------

@app.get("/api/network/stats", response_model=MidnightNetworkStats)
async def get_network_stats():
    return midnight_client.get_network_stats()


@app.get("/api/network/blocks", response_model=List[MidnightBlockModel])
async def get_recent_blocks(limit: int = Query(20, ge=1, le=50)):
    return midnight_client.blocks[-limit:]


@app.get("/api/network/balances/{address}")
async def get_address_balance(address: str):
    balance = midnight_client.shielded_balances.get(address, 50000)
    return {
        "address": address,
        "shielded_balance_night": balance,
        "dust_capacity": balance * 100,
        "is_shielded": address.startswith("midnight1z_")
    }


# -----------------------------------------------------------------------------
# REST API Endpoints: Clinical Trials
# -----------------------------------------------------------------------------

@app.get("/api/trials", response_model=List[ClinicalTrialModel])
async def list_trials():
    return midnight_client.get_all_trials()


@app.get("/api/trials/{trial_id}", response_model=ClinicalTrialModel)
async def get_trial_details(trial_id: str):
    trial = midnight_client.get_trial_by_id(trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Clinical trial not found")
    return trial


@app.post("/api/trials")
async def create_trial(payload: Dict[str, Any]):
    trial_id = f"0x{secrets.token_hex(32)}"
    now = int(time.time())
    
    biomarker = payload.get("required_biomarker", "HER2_POS_EXON20")
    b_hash = compute_biomarker_hash(biomarker)
    excl_conds = payload.get("excluded_conditions", [])
    excl_mask = compute_condition_mask(excl_conds)

    criteria = EligibilityCriteriaModel(
        min_age=int(payload.get("min_age", 21)),
        max_age=int(payload.get("max_age", 65)),
        required_biomarker=biomarker,
        required_biomarker_hash=b_hash,
        min_egfr_level=int(payload.get("min_egfr_level", 60)),
        max_blood_pressure_systolic=int(payload.get("max_blood_pressure_systolic", 140)),
        excluded_conditions=excl_conds,
        excluded_conditions_mask=excl_mask
    )

    max_p = int(payload.get("max_participants", 50))
    reward = int(payload.get("milestone_reward_night", 5000))
    deposit = int(payload.get("escrow_deposit_night", max_p * reward))

    new_trial = ClinicalTrialModel(
        trial_id=trial_id,
        title=payload.get("title", "New Midnight ZK Protocol Trial"),
        sponsor_name=payload.get("sponsor_name", "Clinical Research Sponsor"),
        sponsor_address=payload.get("sponsor_address", f"midnight1q_sponsor_{secrets.token_hex(4)}"),
        phase=payload.get("phase", "Phase II"),
        therapeutic_area=payload.get("therapeutic_area", "Oncology"),
        description=payload.get("description", "Zero-Knowledge clinical protocol hosted on Midnight."),
        criteria=criteria,
        max_participants=max_p,
        enrolled_count=0,
        escrow_deposit_night=deposit,
        milestone_reward_night=reward,
        creation_timestamp=now,
        contract_address="midnight1q_bioveil_zk_c4109fa8"
    )

    success, msg, tx = midnight_client.register_new_trial(new_trial)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {
        "success": True,
        "message": msg,
        "trial": new_trial,
        "tx": tx
    }


# -----------------------------------------------------------------------------
# REST API Endpoints: Zero-Knowledge Prover & Patient Portal
# -----------------------------------------------------------------------------

@app.get("/api/patients/samples")
async def get_sample_patient_profiles():
    return sample_patients


@app.post("/api/zk/generate-proof", response_model=ZKProofData)
async def generate_zk_proof(req: ZKProofGenerationRequest):
    trial = midnight_client.get_trial_by_id(req.trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found for ZK proof generation")

    proof_data = BioVeilZKProver.generate_proof(
        trial_id=req.trial_id,
        criteria=trial.criteria,
        patient=req.patient_profile,
        current_block=midnight_client.current_block_height
    )
    return proof_data


@app.post("/api/zk/submit-proof")
async def submit_zk_proof(req: ZKProofSubmissionRequest):
    # 1. On-Chain Compact Verifier Check
    is_valid, reason = BioVeilZKVerifier.verify_on_chain(
        trial_id=req.trial_id,
        nullifier_hash=req.nullifier_hash,
        public_commitment=req.public_commitment,
        proof_bytes_hex=req.proof_bytes_hex
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"On-chain ZK verification failed: {reason}")

    # 2. Submit to Midnight Dual-State Ledger
    success, msg, tx = midnight_client.submit_zk_enrollment(
        trial_id=req.trial_id,
        nullifier_hash=req.nullifier_hash,
        public_commitment=req.public_commitment,
        proof_bytes_hex=req.proof_bytes_hex,
        shielded_address=req.shielded_address
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    # Broadcast real-time update
    await ws_manager.broadcast({
        "type": "NEW_ZK_ENROLLMENT",
        "trial_id": req.trial_id,
        "nullifier_hash": req.nullifier_hash,
        "tx": tx.model_dump() if tx else None
    })

    return {
        "success": True,
        "message": msg,
        "nullifier_hash": req.nullifier_hash,
        "transaction": tx
    }


# -----------------------------------------------------------------------------
# REST API Endpoints: Shielded Escrow & Milestone Claim
# -----------------------------------------------------------------------------

@app.post("/api/escrow/claim-milestone", response_model=MilestoneClaimResponse)
async def claim_milestone(req: MilestoneClaimRequest):
    success, msg, amount, tx = midnight_client.claim_milestone_payout(
        nullifier_hash=req.nullifier_hash,
        checkpoint_id=req.checkpoint_id,
        completion_secret_hex=req.completion_secret_hex,
        shielded_recipient_address=req.shielded_recipient_address
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return MilestoneClaimResponse(
        success=True,
        transaction_hash=tx.tx_hash if tx else "0x00",
        disbursed_amount_night=amount,
        recipient_address=req.shielded_recipient_address,
        block_height=tx.block_height if tx else midnight_client.current_block_height,
        message=msg
    )


# -----------------------------------------------------------------------------
# REST API Endpoints: Clinical Intelligence, Pharmacovigilance & Bayesian Models
# -----------------------------------------------------------------------------

@app.post("/api/clinical/pharmacovigilance-check")
async def check_pharmacovigilance(payload: Dict[str, Any]):
    trial_drug = payload.get("trial_drug", "CAR_T_CELL_THERAPY")
    medications = payload.get("medications", [])
    is_safe, warnings, commitment = ClinicalPharmacovigilanceSentinel.check_interaction_safety(
        trial_drug=trial_drug,
        patient_medications=medications
    )
    return {
        "is_safe": is_safe,
        "warnings": warnings,
        "zk_safety_commitment": commitment,
        "checked_drug": trial_drug,
        "medication_count_blinded": len(medications)
    }


@app.get("/api/clinical/bayesian-trajectory")
async def get_bayesian_trajectory(
    baseline_egfr: float = Query(92.0, ge=10.0, le=150.0),
    weeks: int = Query(12, ge=2, le=52)
):
    return BayesianBiomarkerTrajectoryEngine.forecast_checkpoint_adherence(
        baseline_egfr=baseline_egfr,
        weeks_in_trial=weeks
    )


@app.post("/api/clinical/mcda-trial-ranking")
async def rank_trials_mcda(patient: PatientEHRProfile):
    all_trials = midnight_client.get_all_trials()
    ranked = MCDAClinicalTrialMatcher.rank_trials_for_patient(patient, all_trials)
    return {
        "patient_id": patient.patient_id,
        "ranked_trials": ranked,
        "scoring_methodology": "MCDA (Genomic 40% | Safety 25% | Escrow 20% | Feasibility 15%)"
    }


# -----------------------------------------------------------------------------
# REST API Endpoints: Compliance & Auditor Viewing Keys
# -----------------------------------------------------------------------------

@app.get("/api/auditor/grants")
async def list_audit_grants():
    return list(audit_manager.grants.values())


@app.post("/api/auditor/grants")
async def create_audit_grant(req: AuditGrantRequest):
    grant = audit_manager.issue_grant(req)
    return {
        "success": True,
        "grant": grant,
        "message": "Audit viewing grant registered on Midnight ledger."
    }


@app.get("/api/auditor/inspect/{grant_id}", response_model=AuditorVerificationResponse)
async def inspect_cohort_audit(grant_id: str):
    grant = audit_manager.grants.get(grant_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Audit grant not found")
    
    trial = midnight_client.get_trial_by_id(grant["trial_id"])
    enrolled = trial.enrolled_count if trial else 18

    resp = audit_manager.verify_and_inspect_cohort(
        grant_id=grant_id,
        auditor_address=grant["auditor_address"],
        trial_data=trial,
        enrolled_count=enrolled
    )
    return resp


# -----------------------------------------------------------------------------
# REST API Endpoints: Compact Smart Contract Source & AST Inspector
# -----------------------------------------------------------------------------

@app.get("/api/contracts/compact-source")
async def get_compact_sources():
    sources = {}
    for filename in ["BioVeilZK.compact", "ShieldEscrow.compact", "AuditCompliance.compact", "compiler_config.json"]:
        file_path = CONTRACTS_DIR / filename
        if file_path.exists():
            sources[filename] = file_path.read_text(encoding="utf-8")
    return sources


# -----------------------------------------------------------------------------
# WebSocket: Live Midnight Network Stream
# -----------------------------------------------------------------------------

@app.websocket("/ws/blocks")
async def websocket_blocks(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send current network snapshot immediately
        await websocket.send_json({
            "type": "INITIAL_SNAPSHOT",
            "network_stats": midnight_client.get_network_stats().model_dump(),
            "latest_blocks": [b.model_dump() for b in midnight_client.blocks[-5:]]
        })
        while True:
            # Keep socket alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# -----------------------------------------------------------------------------
# Frontend Static Files & SPA Route
# -----------------------------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "BioVeil ZK Midnight Backend Operational"})
