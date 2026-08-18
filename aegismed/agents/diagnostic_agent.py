"""
Differential Diagnosis Agent
Formulates prioritized diagnostic hypotheses by fusing real-time presentation
with recalled longitudinal episodic memory from CockroachDB.
"""

import logging
from typing import Dict, Any, List
from aegismed.memory.working_memory import WorkingMemoryManager
from aegismed.memory.episodic_memory import EpisodicMemoryManager
from aegismed.providers.local_fallback import LocalAIProvider
from aegismed.providers.gateway import gateway

logger = logging.getLogger("aegismed.diagnostic_agent")


class DiagnosticAgent:
    """Agent responsible for clinical differential diagnosis and episodic synthesis."""

    def __init__(self, working_memory: WorkingMemoryManager, episodic_memory: EpisodicMemoryManager):
        self.working = working_memory
        self.episodic = episodic_memory
        self.name = "DifferentialDiagnosisAgent"
        self.local_ai = LocalAIProvider()

    def generate_differential_diagnosis(
        self,
        session_id: str,
        patient_uid: str,
        chief_complaint: str,
        symptoms: List[str],
        vitals: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recalls episodic memories from CockroachDB and generates differential diagnoses."""
        presentation_query = f"{chief_complaint} {' '.join(symptoms)}"
        
        # 1. Recall relevant past episodes from CockroachDB
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=f"Querying CockroachDB Episodic Vector Memory for patient '{patient_uid}' matching presentation...",
            step_type="EPISODIC_RECALL"
        )
        
        recalled_episodes = self.episodic.recall_relevant_episodes(
            patient_uid=patient_uid,
            current_presentation=presentation_query,
            top_k=3
        )
        
        recall_summary = f"Retrieved {len(recalled_episodes)} historical encounter(s) from CockroachDB."
        if recalled_episodes:
            top_ep = recalled_episodes[0]
            recall_summary += f" Top match: '{top_ep.get('diagnosis', 'Encounter')}' (Similarity: {top_ep.get('vector_similarity', 0.0):.2f})."
            
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=recall_summary,
            step_type="EPISODIC_EVIDENCE"
        )

        # 2. Formulate Differential Diagnosis
        hypotheses = self.local_ai.simulate_differential_diagnosis(
            chief_complaint=chief_complaint,
            symptoms=symptoms,
            vitals=vitals,
            episodic_memories=recalled_episodes
        )

        hypo_text = "Generated Differential Diagnoses:\n" + "\n".join([
            f"- {h['condition']} (Probability: {int(h['probability']*100)}%)" for h in hypotheses
        ])
        
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=hypo_text,
            step_type="DIAGNOSTIC_HYPOTHESIS"
        )

        # Update working session hypotheses
        self.working.update_working_state(
            session_id=session_id,
            hypotheses=hypotheses,
            context_updates={"recalled_episodes": recalled_episodes}
        )

        return hypotheses
