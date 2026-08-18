"""
Autonomous Reflection & Audit Agent
Runs meta-analysis on long-term clinical trajectories and saves actionable meta-insights in CockroachDB.
"""

import logging
from typing import Dict, Any, List
from aegismed.memory.working_memory import WorkingMemoryManager
from aegismed.memory.reflective_memory import ReflectiveMemoryManager
from sqlalchemy.orm import Session

logger = logging.getLogger("aegismed.reflection_agent")


class ReflectionAgent:
    """Agent that performs asynchronous meta-reflection and historical synthesis."""

    def __init__(self, db: Session, working_memory: WorkingMemoryManager, reflective_memory: ReflectiveMemoryManager):
        self.db = db
        self.working = working_memory
        self.reflective = reflective_memory
        self.name = "ReflectionAuditAgent"

    def execute_reflection(self, session_id: str, patient_uid: str) -> List[Dict[str, Any]]:
        """Executes meta-reflection across historical patient episodes."""
        self.working.record_agent_thought(
            session_id=session_id,
            agent_name=self.name,
            thought_text=f"Initiating autonomous Tier-4 Meta-Reflection across all historical episodes for {patient_uid}...",
            step_type="REFLECTION_START"
        )

        insights = self.reflective.generate_patient_reflections(patient_uid)
        
        serialized_insights = []
        for ins in insights:
            serialized_insights.append({
                "insight_uid": ins.insight_uid,
                "type": ins.insight_type,
                "headline": ins.headline,
                "synthesis": ins.detailed_synthesis,
                "confidence": ins.confidence_score,
                "guidance": ins.actionable_guidance
            })

        if insights:
            summary_msg = f"Reflective synthesis complete. Generated/Retrieved {len(insights)} meta-insight(s):\n"
            for ins in insights:
                summary_msg += f"• [{ins.insight_type}] {ins.headline} (Confidence: {int(ins.confidence_score*100)}%)\n"
            
            self.working.record_agent_thought(
                session_id=session_id,
                agent_name=self.name,
                thought_text=summary_msg,
                step_type="REFLECTION_SYNTHESIS"
            )
        else:
            self.working.record_agent_thought(
                session_id=session_id,
                agent_name=self.name,
                thought_text="No anomalous longitudinal drift detected across historical episodes.",
                step_type="REFLECTION_CLEAN"
            )

        # Update working session
        self.working.update_working_state(
            session_id=session_id,
            context_updates={"reflective_insights": serialized_insights}
        )

        return serialized_insights
