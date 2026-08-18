"""
Tier 3: Semantic Medical Guidelines & Contraindication Knowledge Base
Maintains domain-specific medical knowledge, drug interaction ontologies,
and clinical practice guidelines indexed with CockroachDB vector search.
"""

import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from aegismed.database.models import SemanticGuideline
from aegismed.memory.cockroach_store import CockroachMemoryStore
from aegismed.providers.gateway import gateway

logger = logging.getLogger("aegismed.semantic_memory")


class SemanticMemoryManager:
    """Manages domain-level medical knowledge and safety guidelines."""

    def __init__(self, db: Session):
        self.db = db
        self.store = CockroachMemoryStore(db)

    def register_guideline(
        self,
        category: str,
        title: str,
        entity_a: str,
        entity_b: str,
        description: str,
        clinical_recommendation: str,
        risk_level: str = "HIGH",
        source_authority: str = "FDA / Clinical Practice Guidelines"
    ) -> SemanticGuideline:
        """Adds a clinical guideline or contraindication rule with vector indexing."""
        rule_uid = f"rule_{uuid.uuid4().hex[:12]}"
        vector_text = f"Medical Guideline: {title}. {category}. Entities: {entity_a} and {entity_b}. Risk: {risk_level}. Description: {description}. Recommendation: {clinical_recommendation}"
        embedding_vec = gateway.get_embedding(vector_text)

        guideline = SemanticGuideline(
            rule_uid=rule_uid,
            category=category,
            title=title,
            entity_a=entity_a,
            entity_b=entity_b,
            risk_level=risk_level,
            description=description,
            clinical_recommendation=clinical_recommendation,
            source_authority=source_authority,
            embedding=embedding_vec
        )
        self.db.add(guideline)
        self.db.commit()
        self.db.refresh(guideline)
        return guideline

    def check_contraindications(
        self,
        candidate_medications: List[str],
        known_allergies: List[str],
        chronic_conditions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Cross-references candidate medications against patient allergies, chronic diseases,
        and known drug interactions using semantic memory rules.
        """
        alerts = []
        all_patient_entities = [a.lower() for a in (known_allergies or [])] + [c.lower() for c in (chronic_conditions or [])]

        for med in candidate_medications:
            med_clean = med.strip().lower()
            
            # Check 1: Direct Allergy Matching (e.g. Penicillin vs Amoxicillin / Ampicillin)
            if "penicillin" in all_patient_entities:
                if any(p in med_clean for p in ["amoxicillin", "ampicillin", "penicillin", "augmentin", "piperacillin"]):
                    alerts.append({
                        "risk_level": "CRITICAL",
                        "category": "DRUG_ALLERGY_CONTRAINDICATION",
                        "title": f"Fatal Allergic Cross-Reactivity: {med.title()} in Penicillin-Allergic Patient",
                        "offending_agent": med,
                        "conflicting_condition_or_allergy": "Documented Penicillin Allergy",
                        "mechanism": "Beta-lactam core structure triggers severe hypersensitivity / anaphylaxis.",
                        "actionable_alternative": "Switch to Macrolides (Azithromycin) or Fluoroquinolones (Levofloxacin).",
                        "source": "FDA Safety Alerts / CockroachDB Semantic Memory"
                    })

            # Check 2: Semantic Database Rule Search
            results = self.store.search_semantic_guidelines(
                query_text=f"Contraindications for {med} with {', '.join(all_patient_entities)}",
                entities=[med] + known_allergies + chronic_conditions,
                top_k=3
            )
            for rule, score in results:
                if rule.entity_a.lower() in [med_clean] + all_patient_entities or \
                   rule.entity_b.lower() in [med_clean] + all_patient_entities:
                    alerts.append({
                        "risk_level": rule.risk_level,
                        "category": rule.category,
                        "title": rule.title,
                        "offending_agent": med,
                        "conflicting_condition_or_allergy": f"{rule.entity_a} / {rule.entity_b}",
                        "mechanism": rule.description,
                        "actionable_alternative": rule.clinical_recommendation,
                        "source": rule.source_authority,
                        "similarity_score": round(score, 4)
                    })

        # Deduplicate alerts by title
        unique_alerts = []
        seen = set()
        for a in alerts:
            if a["title"] not in seen:
                seen.add(a["title"])
                unique_alerts.append(a)

        return unique_alerts
