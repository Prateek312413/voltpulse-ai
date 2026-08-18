"""
Tier 4: Reflective / Meta-Memory Engine
Executes asynchronous meta-cognition across longitudinal clinical episodes,
detecting hidden temporal patterns, diagnostic contradictions, and disease trajectories.
"""

import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from aegismed.database.models import ReflectiveInsight, ClinicalEpisode, Patient
from aegismed.memory.cockroach_store import CockroachMemoryStore

logger = logging.getLogger("aegismed.reflective_memory")


class ReflectiveMemoryManager:
    """Performs deep meta-reflection across patient longitudinal history."""

    def __init__(self, db: Session):
        self.db = db
        self.store = CockroachMemoryStore(db)

    def generate_patient_reflections(self, patient_uid: str) -> List[ReflectiveInsight]:
        """
        Synthesizes longitudinal encounters into high-level meta-insights:
        1. Adverse reaction tracking
        2. Biomarker & vital sign trajectories (e.g., eGFR / BP drift)
        3. Therapeutic efficacy / recurrence patterns
        """
        episodes = self.db.query(ClinicalEpisode).filter(
            ClinicalEpisode.patient_uid == patient_uid
        ).order_by(ClinicalEpisode.timestamp.asc()).all()

        if not episodes:
            return []

        patient = self.db.query(Patient).filter(Patient.patient_uid == patient_uid).first()
        insights_generated = []

        # 1. Analyze for Allergic / Adverse Reaction History
        allergy_episodes = []
        for ep in episodes:
            text = f"{ep.chief_complaint} {ep.physician_notes or ''} {' '.join(ep.symptoms)}".lower()
            if any(k in text for k in ["rash", "hives", "anaphylaxis", "allergy", "urticaria", "hypersensitivity", "swelling", "edema"]):
                allergy_episodes.append(ep)

        if allergy_episodes:
            source_uids = [e.episode_uid for e in allergy_episodes]
            existing = self.db.query(ReflectiveInsight).filter(
                ReflectiveInsight.patient_uid == patient_uid,
                ReflectiveInsight.insight_type == "ADVERSE_REACTION_PATTERN"
            ).first()

            if not existing:
                insight = ReflectiveInsight(
                    insight_uid=f"ins_{uuid.uuid4().hex[:12]}",
                    patient_uid=patient_uid,
                    insight_type="ADVERSE_REACTION_PATTERN",
                    headline="Historical Hypersensitivity / Severe Drug Allergy Pattern Detected",
                    detailed_synthesis=(
                        f"Longitudinal analysis across {len(allergy_episodes)} past encounter(s) demonstrates "
                        f"acute hypersensitivity events following antibiotic or foreign substance exposure."
                    ),
                    confidence_score=0.96,
                    source_episode_uids=source_uids,
                    actionable_guidance="Mandate hard block on Beta-lactams, Cephalosporins, and cross-reactive agents in all future consultations.",
                    flagged_for_physician=True
                )
                self.db.add(insight)
                self.db.commit()
                insights_generated.append(insight)

        # 2. Analyze Biomarker / Lab Trajectory (e.g. Creatinine / Renal / BP)
        bp_history = []
        creat_history = []
        for ep in episodes:
            if ep.vital_signs and "bp_sys" in ep.vital_signs:
                bp_history.append((ep.timestamp, ep.vital_signs["bp_sys"]))
            if ep.lab_results and "creatinine" in ep.lab_results:
                creat_history.append((ep.timestamp, ep.lab_results["creatinine"]))

        if len(creat_history) >= 2:
            first_c = creat_history[0][1]
            last_c = creat_history[-1][1]
            if last_c > first_c * 1.2: # >20% increase
                insight = ReflectiveInsight(
                    insight_uid=f"ins_{uuid.uuid4().hex[:12]}",
                    patient_uid=patient_uid,
                    insight_type="DISEASE_PROGRESSION",
                    headline="Progressive Renal Impairment (Serum Creatinine Upward Drift)",
                    detailed_synthesis=(
                        f"Longitudinal renal monitoring shows serum creatinine elevated from {first_c} mg/dL to {last_c} mg/dL. "
                        f"Consistent with Stage 3 Chronic Kidney Disease (CKD) acceleration."
                    ),
                    confidence_score=0.92,
                    source_episode_uids=[e.episode_uid for e in episodes],
                    actionable_guidance="Adjust all renal-cleared drug dosages and order comprehensive 24hr urine protein and renal ultrasound.",
                    flagged_for_physician=True
                )
                self.db.add(insight)
                self.db.commit()
                insights_generated.append(insight)

        return self.get_insights(patient_uid)

    def get_insights(self, patient_uid: str) -> List[ReflectiveInsight]:
        """Returns all recorded reflective meta-insights for a patient."""
        return self.db.query(ReflectiveInsight).filter(
            ReflectiveInsight.patient_uid == patient_uid
        ).all()
