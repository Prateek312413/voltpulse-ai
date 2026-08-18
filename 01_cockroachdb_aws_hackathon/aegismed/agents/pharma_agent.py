"""
Pharmacovigilance & Contraindication Agent
Ensures patient safety by cross-referencing candidate prescriptions against
CockroachDB Semantic Memory guidelines, patient allergies, and historical adverse episodes.
"""

import logging
from typing import Dict, Any, List
from aegismed.memory.working_memory import WorkingMemoryManager
from aegismed.memory.semantic_memory import SemanticMemoryManager
from aegismed.database.models import Patient
from sqlalchemy.orm import Session

logger = logging.getLogger("aegismed.pharma_agent")


class PharmacovigilanceAgent:
    """Agent that performs multi-tiered safety audits to prevent medical errors."""

    def __init__(self, db: Session, working_memory: WorkingMemoryManager, semantic_memory: SemanticMemoryManager):
        self.db = db
        self.working = working_memory
        self.semantic = semantic_memory
        self.name = "PharmacovigilanceAgent"

    def perform_safety_audit(
        self,
        session_id: str,
        patient_uid: str,
        candidate_medications: List[str]
    ) -> Dict[str, Any]:
        """Conducts safety audit across CockroachDB memory tiers."""
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=f"Initiating safety verification for candidate drugs: {candidate_medications}",
            step_type="SAFETY_AUDIT_START"
        )

        patient = self.db.query(Patient).filter(Patient.patient_uid == patient_uid).first()
        allergies = patient.allergies if patient else []
        conditions = patient.chronic_conditions if patient else []

        alerts = self.semantic.check_contraindications(
            candidate_medications=candidate_medications,
            known_allergies=allergies,
            chronic_conditions=conditions
        )

        approved_medications = []
        blocked_medications = []

        for med in candidate_medications:
            is_blocked = any(a.get("offending_agent", "").lower() in med.lower() and a.get("risk_level") in ["CRITICAL", "HIGH"] for a in alerts)
            if is_blocked:
                blocked_medications.append(med)
            else:
                approved_medications.append(med)

        if alerts:
            alert_msg = f"⚠️ SAFETY ALERT: Detected {len(alerts)} contraindication/allergy conflict(s) in CockroachDB memory:\n"
            for a in alerts:
                alert_msg += f"• [{a['risk_level']}] {a['title']} -> {a['actionable_alternative']}\n"
            
            self.working.record_agent_thought(
                session_id=session_id,
                agent_name=self.name,
                thought_text=alert_msg,
                step_type="CONTRAINDICATION_ALERT"
            )
        else:
            self.working.record_agent_thought(
                session_id=session_id,
                agent_name=self.name,
                thought_text=f"✓ All candidate medications verified safe against patient memory profile.",
                step_type="SAFETY_VERIFIED"
            )

        safety_report = {
            "safety_passed": len(blocked_medications) == 0,
            "alerts": alerts,
            "approved_medications": approved_medications,
            "blocked_medications": blocked_medications
        }

        # Update working session
        self.working.update_working_state(
            session_id=session_id,
            safety_checks=alerts,
            context_updates={"safety_audit_report": safety_report}
        )

        return safety_report
