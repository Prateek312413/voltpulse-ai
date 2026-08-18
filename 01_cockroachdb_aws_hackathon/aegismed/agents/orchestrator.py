"""
Multi-Agent Clinical Swarm Orchestrator
Coordinates lock arbitration, sequential deliberation, safety consensus,
and persistent memory consolidation in CockroachDB.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from aegismed.memory import AgenticMemoryEngine, MemoryGraph
from aegismed.agents.triage_agent import TriageAgent
from aegismed.agents.diagnostic_agent import DiagnosticAgent
from aegismed.agents.pharma_agent import PharmacovigilanceAgent
from aegismed.agents.reflection_agent import ReflectionAgent
from aegismed.database.models import Patient

logger = logging.getLogger("aegismed.orchestrator")


class SwarmOrchestrator:
    """Orchestrates multi-agent consensus workflows with CockroachDB persistent memory."""

    def __init__(self, db: Session):
        self.db = db
        self.memory = AgenticMemoryEngine(db)
        self.triage = TriageAgent(self.memory.working)
        self.diagnostic = DiagnosticAgent(self.memory.working, self.memory.episodic)
        self.pharma = PharmacovigilanceAgent(db, self.memory.working, self.memory.semantic)
        self.reflection = ReflectionAgent(db, self.memory.working, self.memory.reflective)

    def run_consultation_swarm(
        self,
        patient_uid: str,
        chief_complaint: str,
        symptoms: List[str],
        vitals: Dict[str, Any],
        physician_notes: str = "",
        save_as_episode: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent clinical consultation workflow with ACID transactional state.
        """
        start_time = time.time()
        
        # 1. Initialize Working Memory Session
        session = self.memory.working.initialize_session(
            patient_uid=patient_uid,
            initial_data={
                "chief_complaint": chief_complaint,
                "symptoms": symptoms,
                "vitals": vitals,
                "physician_notes": physician_notes
            }
        )
        session_id = session.session_id

        # 2. Acquire Distributed Lock for Triage Agent
        self.memory.working.acquire_lock(session_id, "TriageAgent")
        triage_out = self.triage.execute_triage(
            session_id=session_id,
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            vitals=vitals
        )
        self.memory.working.release_lock(session_id, "TriageAgent")

        # 3. Acquire Lock for Diagnostic Agent
        self.memory.working.acquire_lock(session_id, "DiagnosticAgent")
        hypotheses = self.diagnostic.generate_differential_diagnosis(
            session_id=session_id,
            patient_uid=patient_uid,
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            vitals=vitals
        )
        self.memory.working.release_lock(session_id, "DiagnosticAgent")

        # Gather candidate medications from top hypotheses
        candidate_meds = []
        for h in hypotheses:
            candidate_meds.extend(h.get("proposed_medications", []))
        candidate_meds = list(dict.fromkeys(candidate_meds)) # Deduplicate

        # 4. Acquire Lock for Pharmacovigilance Agent
        self.memory.working.acquire_lock(session_id, "PharmacovigilanceAgent")
        safety_report = self.pharma.perform_safety_audit(
            session_id=session_id,
            patient_uid=patient_uid,
            candidate_medications=candidate_meds
        )
        self.memory.working.release_lock(session_id, "PharmacovigilanceAgent")

        # 5. Acquire Lock for Reflection Agent
        self.memory.working.acquire_lock(session_id, "ReflectionAgent")
        insights = self.reflection.execute_reflection(
            session_id=session_id,
            patient_uid=patient_uid
        )
        self.memory.working.release_lock(session_id, "ReflectionAgent")

        # 6. Primary Recommended Diagnosis & Treatment Plan
        top_dx = hypotheses[0] if hypotheses else {"condition": "Undifferentiated Acute Symptoms", "icd10": "R68.89", "probability": 0.5}
        
        # Determine final prescribed medications (only approved medications)
        approved_meds = safety_report.get("approved_medications", [])
        final_med_plan = [{"name": m, "dose": "Standard adult dose", "freq": "Daily as directed"} for m in approved_meds]

        # 7. Optionally Commit to Tier-2 Episodic Memory in CockroachDB
        new_episode = None
        if save_as_episode:
            new_episode = self.memory.episodic.record_episode(
                patient_uid=patient_uid,
                chief_complaint=chief_complaint,
                symptoms=symptoms,
                diagnosis=top_dx.get("condition"),
                prescribed_medications=final_med_plan,
                vital_signs=vitals,
                physician_notes=f"Consultation completed by AegisMed Swarm. Safety validated. Flags: {len(safety_report.get('alerts', []))}",
                severity_score=triage_out.get("urgency_score", 1.0)
            )

        duration = (time.time() - start_time) * 1000.0

        # 8. Generate Visual Memory Graph
        memory_graph = self.memory.generate_memory_graph(patient_uid=patient_uid, session_id=session_id)

        # Refresh working session to get full thought history
        sess_refreshed = self.memory.working.get_session(session_id)
        thoughts = sess_refreshed.agent_thoughts if sess_refreshed else []

        return {
            "session_id": session_id,
            "patient_uid": patient_uid,
            "execution_time_ms": round(duration, 2),
            "triage": triage_out,
            "differential_diagnoses": hypotheses,
            "safety_audit": safety_report,
            "reflective_insights": insights,
            "primary_diagnosis": top_dx,
            "final_treatment_plan": final_med_plan,
            "agent_thoughts": thoughts,
            "memory_graph": memory_graph.model_dump(),
            "new_episode_uid": new_episode.episode_uid if new_episode else None
        }
