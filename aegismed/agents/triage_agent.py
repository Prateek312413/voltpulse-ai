"""
Clinical Triage Agent
Performs rapid acuity stratification, validates vital signs, and seeds Working Memory state.
"""

import logging
from typing import Dict, Any, List
from aegismed.memory.working_memory import WorkingMemoryManager
from aegismed.providers.local_fallback import LocalAIProvider

logger = logging.getLogger("aegismed.triage_agent")


class TriageAgent:
    """Agent responsible for initial patient intake and acuity stratification."""

    def __init__(self, working_memory: WorkingMemoryManager):
        self.working = working_memory
        self.name = "ClinicalTriageAgent"
        self.local_ai = LocalAIProvider()

    def execute_triage(
        self,
        session_id: str,
        chief_complaint: str,
        symptoms: List[str],
        vitals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Runs triage analysis, logs reasoning steps, and locks working memory state."""
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=f"Initiating triage protocol for presentation: '{chief_complaint}' with {len(symptoms)} reported symptoms.",
            step_type="INTAKE"
        )

        # Calculate clinical acuity
        triage_result = self.local_ai.simulate_triage_decision(symptoms, vitals, chief_complaint)
        acuity = triage_result["acuity"]
        urgency = triage_result["urgency_score"]

        thought_msg = (
            f"Acuity assessed as [{acuity}] (Urgency Score: {urgency}/5.0). "
            f"Flags: {', '.join(triage_result['clinical_flags']) if triage_result['clinical_flags'] else 'None'}. "
            f"Routing to Diagnostic and Pharmacovigilance agents."
        )
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=thought_msg,
            step_type="TRIAGE_ASSESSMENT"
        )

        # Update working session state
        self.working.update_working_state(
            session_id=session_id,
            acuity=acuity,
            context_updates={
                "triage_summary": triage_result,
                "chief_complaint": chief_complaint,
                "symptoms": symptoms,
                "vitals": vitals
            }
        )

        return triage_result
