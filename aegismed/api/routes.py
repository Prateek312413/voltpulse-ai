"""
AegisMed REST API Router
Exposes clinical consultation, multi-agent reasoning, vector search,
and interactive memory graph endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

from aegismed.database.connection import get_db, active_backend
from aegismed.database.models import Patient, ClinicalEpisode, ReflectiveInsight, WorkingMemorySession, SemanticGuideline
from aegismed.database.seed_data import seed_all
from aegismed.memory import AgenticMemoryEngine
from aegismed.agents.orchestrator import SwarmOrchestrator
from aegismed.providers.gateway import gateway
from aegismed.config import settings

router = APIRouter(prefix="/api", tags=["AegisMed Engine"])


# --- Schemas ---

class ConsultationRequest(BaseModel):
    patient_uid: str
    chief_complaint: str
    symptoms: List[str] = Field(default_factory=list)
    vital_signs: Dict[str, Any] = Field(default_factory=lambda: {"bp_sys": 120, "bp_dia": 80, "hr": 72, "spo2": 98, "temp_c": 37.0})
    physician_notes: Optional[str] = ""
    save_to_episodic_memory: bool = True


class VectorSearchRequest(BaseModel):
    patient_uid: str
    query_text: str
    top_k: int = 5


class PatientCreateRequest(BaseModel):
    patient_uid: str
    name: str
    age: int
    gender: str
    blood_type: Optional[str] = "O+"
    allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)


# --- Endpoints ---

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    """System health check, CockroachDB status, and memory metrics."""
    patient_count = db.query(Patient).count()
    episode_count = db.query(ClinicalEpisode).count()
    guideline_count = db.query(SemanticGuideline).count()
    insight_count = db.query(ReflectiveInsight).count()

    return {
        "status": "ONLINE",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "database_backend": active_backend,
        "cockroachdb_connected": active_backend == "COCKROACHDB",
        "aws_bedrock_connected": gateway.bedrock.available,
        "metrics": {
            "total_patients": patient_count,
            "total_episodic_memories": episode_count,
            "total_semantic_guidelines": guideline_count,
            "total_reflective_insights": insight_count
        }
    }


@router.get("/patients")
def list_patients(db: Session = Depends(get_db)):
    """Lists all registered patients and their baseline profiles."""
    patients = db.query(Patient).all()
    results = []
    for p in patients:
        ep_count = db.query(ClinicalEpisode).filter(ClinicalEpisode.patient_uid == p.patient_uid).count()
        ins_count = db.query(ReflectiveInsight).filter(ReflectiveInsight.patient_uid == p.patient_uid).count()
        results.append({
            "patient_uid": p.patient_uid,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "blood_type": p.blood_type,
            "allergies": p.allergies or [],
            "chronic_conditions": p.chronic_conditions or [],
            "episode_count": ep_count,
            "insight_count": ins_count
        })
    return {"patients": results}


@router.get("/patients/{patient_uid}")
def get_patient_details(patient_uid: str, db: Session = Depends(get_db)):
    """Retrieves full longitudinal history, episodes, and reflective insights."""
    patient = db.query(Patient).filter(Patient.patient_uid == patient_uid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    episodes = db.query(ClinicalEpisode).filter(
        ClinicalEpisode.patient_uid == patient_uid
    ).order_by(ClinicalEpisode.timestamp.desc()).all()

    insights = db.query(ReflectiveInsight).filter(
        ReflectiveInsight.patient_uid == patient_uid
    ).order_by(ReflectiveInsight.created_at.desc()).all()

    return {
        "patient": {
            "patient_uid": patient.patient_uid,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "blood_type": patient.blood_type,
            "allergies": patient.allergies or [],
            "chronic_conditions": patient.chronic_conditions or []
        },
        "episodes": [
            {
                "episode_uid": ep.episode_uid,
                "timestamp": ep.timestamp.isoformat(),
                "encounter_type": ep.encounter_type,
                "chief_complaint": ep.chief_complaint,
                "symptoms": ep.symptoms,
                "diagnosis": ep.diagnosis,
                "prescribed_medications": ep.prescribed_medications,
                "vital_signs": ep.vital_signs,
                "lab_results": ep.lab_results,
                "physician_notes": ep.physician_notes,
                "severity_score": ep.severity_score
            } for ep in episodes
        ],
        "reflective_insights": [
            {
                "insight_uid": ins.insight_uid,
                "insight_type": ins.insight_type,
                "headline": ins.headline,
                "synthesis": ins.detailed_synthesis,
                "confidence_score": ins.confidence_score,
                "actionable_guidance": ins.actionable_guidance,
                "created_at": ins.created_at.isoformat()
            } for ins in insights
        ]
    }


@router.post("/consultation")
def run_consultation(req: ConsultationRequest, db: Session = Depends(get_db)):
    """
    Core Entrypoint: Runs Multi-Agent Swarm with CockroachDB Persistent Memory.
    """
    patient = db.query(Patient).filter(Patient.patient_uid == req.patient_uid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient UID not registered in system.")

    orchestrator = SwarmOrchestrator(db)
    result = orchestrator.run_consultation_swarm(
        patient_uid=req.patient_uid,
        chief_complaint=req.chief_complaint,
        symptoms=req.symptoms,
        vitals=req.vital_signs,
        physician_notes=req.physician_notes or "",
        save_as_episode=req.save_to_episodic_memory
    )
    return result


@router.get("/memory/graph/{patient_uid}")
def get_memory_graph(patient_uid: str, session_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Generates interconnected 4-Tier Memory Graph for live visualization."""
    engine = AgenticMemoryEngine(db)
    graph = engine.generate_memory_graph(patient_uid=patient_uid, session_id=session_id)
    return graph.model_dump()


@router.post("/memory/vector-search")
def vector_search(req: VectorSearchRequest, db: Session = Depends(get_db)):
    """Performs direct semantic vector search against CockroachDB episodic memory."""
    engine = AgenticMemoryEngine(db)
    results = engine.episodic.recall_relevant_episodes(
        patient_uid=req.patient_uid,
        current_presentation=req.query_text,
        top_k=req.top_k
    )
    return {
        "query": req.query_text,
        "patient_uid": req.patient_uid,
        "recalled_memories": results
    }


@router.post("/telemetry/late-sync")
def sync_late_telemetry(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Ingests out-of-order / late-arriving telemetry, re-evaluates longitudinal memory in CockroachDB,
    and returns reconciled Bayesian uncertainty trajectories.
    """
    from aegismed.memory.reconciliation import LateTelemetryReconciler
    patient_uid = payload.get("patient_uid", "P-1002")
    days_ago = payload.get("days_ago", 30)
    delayed_time = datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)

    reconciler = LateTelemetryReconciler(db)
    result = reconciler.ingest_late_telemetry(
        patient_uid=patient_uid,
        delayed_timestamp=delayed_time,
        observation_type=payload.get("observation_type", "Delayed Renal Lab Panel"),
        observation_data=payload.get("observation_data", {"lab_results": {"creatinine": 1.65}}),
        clinical_note=payload.get("note", "Delayed clinical lab synchronized asynchronously.")
    )
    return result


@router.get("/patients/{patient_uid}/trajectory")
def get_patient_biomarker_trajectory(patient_uid: str, db: Session = Depends(get_db)):
    """
    Computes Gaussian Process Bayesian biomarker trajectory and 95% confidence intervals.
    """
    from aegismed.ml.uncertainty_engine import uncertainty_engine
    episodes = db.query(ClinicalEpisode).filter(
        ClinicalEpisode.patient_uid == patient_uid
    ).order_by(ClinicalEpisode.timestamp.asc()).all()

    if not episodes:
        return {"error": "No historical episodes found"}

    base_time = episodes[0].timestamp
    time_points = []
    creat_values = []

    for ep in episodes:
        if ep.lab_results and "creatinine" in ep.lab_results:
            days = (ep.timestamp - base_time).total_seconds() / 86400.0
            time_points.append(days)
            creat_values.append(float(ep.lab_results["creatinine"]))

    if len(time_points) < 2:
        time_points = [0.0, 90.0]
        creat_values = [1.1, 1.3]

    forecast = uncertainty_engine.forecast_biomarker_trajectory(
        time_points_days=time_points,
        biomarker_values=creat_values,
        forecast_horizon_days=90
    )

    return {
        "patient_uid": patient_uid,
        "historical_days": time_points,
        "historical_values": creat_values,
        "forecast": forecast
    }


@router.post("/seed-benchmark")
def seed_benchmark():
    """Re-seeds benchmark clinical scenarios and guidelines."""
    seed_all()
    return {"message": "Successfully seeded benchmark clinical scenarios into CockroachDB."}
