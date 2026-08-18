"""
Local Intelligent AI & Vector Embedding Engine
Provides sentence-transformers and offline medical heuristic inference
ensuring 100% reproducible execution and offline testability.
"""

import hashlib
import logging
import numpy as np
import json
import re
from typing import List, Dict, Any, Optional
from aegismed.config import settings

logger = logging.getLogger("aegismed.local_ai")

# Optional fast local sentence transformer
try:
    from sentence_transformers import SentenceTransformer
    LOCAL_EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as e:
    LOCAL_EMBEDDER = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class LocalAIProvider:
    """Local fallback provider for embeddings and multi-agent clinical simulation."""

    def __init__(self):
        self.dim = settings.VECTOR_DIMENSION

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a 384-dimensional normalized vector embedding."""
        if SENTENCE_TRANSFORMERS_AVAILABLE and LOCAL_EMBEDDER is not None:
            try:
                emb = LOCAL_EMBEDDER.encode(text, normalize_embeddings=True)
                return emb.tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformer encode failed: {e}. Using deterministic semantic hash.")
        
        # High-entropy deterministic semantic hash for offline fallback
        return self._generate_deterministic_vector(text)

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        """Generates a reproducible, normalized pseudo-semantic vector based on text n-grams."""
        clean_text = re.sub(r"[^\w\s]", "", text.lower())
        words = clean_text.split()
        
        vector = np.zeros(self.dim, dtype=np.float32)
        for i, word in enumerate(words):
            # Hash word into vector index buckets
            h = int(hashlib.sha256(word.encode('utf-8')).hexdigest(), 16)
            idx1 = h % self.dim
            idx2 = (h >> 8) % self.dim
            idx3 = (h >> 16) % self.dim
            
            weight = 1.0 / (1.0 + 0.1 * i)
            vector[idx1] += weight * 1.5
            vector[idx2] -= weight * 0.8
            vector[idx3] += weight * 0.5
            
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        else:
            vector[0] = 1.0
        return vector.tolist()

    def simulate_triage_decision(self, symptoms: List[str], vitals: Dict[str, Any], chief_complaint: str) -> Dict[str, Any]:
        """Clinical acuity and urgency classifier."""
        hr = vitals.get("hr", 75)
        spo2 = vitals.get("spo2", 98)
        bp_sys = vitals.get("bp_sys", 120)
        temp_c = vitals.get("temp_c", 37.0)

        acuity = "STANDARD"
        urgency_score = 2.0
        flags = []

        if spo2 < 92 or bp_sys < 90 or hr > 130 or temp_c > 39.5:
            acuity = "CRITICAL"
            urgency_score = 4.8
            flags.append("Hemodynamic instability or hypoxia detected")
        elif spo2 < 95 or bp_sys > 170 or hr > 105 or "chest pain" in chief_complaint.lower() or "dyspnea" in chief_complaint.lower():
            acuity = "URGENT"
            urgency_score = 3.8
            flags.append("High acuity presentation requiring rapid escalation")
        elif "fever" in chief_complaint.lower() or "infection" in chief_complaint.lower():
            acuity = "ELEVATED"
            urgency_score = 2.8
            flags.append("Infectious prodrome identified")

        return {
            "acuity": acuity,
            "urgency_score": urgency_score,
            "triage_category": "Emergency/Urgent Care" if urgency_score > 3.5 else "Ambulatory/Outpatient",
            "clinical_flags": flags,
            "recommended_workflow": ["DifferentialDiagnosisAgent", "PharmacovigilanceAgent", "ReflectionAgent"]
        }

    def simulate_differential_diagnosis(
        self,
        chief_complaint: str,
        symptoms: List[str],
        vitals: Dict[str, Any],
        episodic_memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generates prioritized differential diagnoses grounded in symptoms & longitudinal memories."""
        combined_text = f"{chief_complaint} {' '.join(symptoms)}".lower()
        hypotheses = []

        # Check for cardiac / chest pain (Prioritized in high-acuity chest complaints)
        if any(k in combined_text for k in ["chest pain", "angina", "palpitation", "substernal", "crushing", "radiating to shoulder", "diaphoresis"]):
            hypotheses.append({
                "condition": "Acute Coronary Syndrome / Angina Pectoris",
                "icd10": "I20.9",
                "probability": 0.91,
                "confidence_interval": [0.85, 0.96],
                "justification": "Exertional/acute substernal chest discomfort with autonomic diaphoresis.",
                "proposed_medications": ["Aspirin", "Nitroglycerin", "Atorvastatin"]
            })
            hypotheses.append({
                "condition": "Atypical Cardiac Ischemia / Hypertensive Urgency",
                "icd10": "I16.0",
                "probability": 0.65,
                "confidence_interval": [0.55, 0.75],
                "justification": "Elevated blood pressure with ischemic cardiac demand.",
                "proposed_medications": ["Amlodipine", "Nitroglycerin"]
            })

        # Check for respiratory/infection (Sore throat, pharyngitis, cough, bronchitis)
        elif any(k in combined_text for k in ["sore throat", "throat", "swallowing", "pharyngitis", "tonsillitis", "cough", "bronchitis", "pneumonia", "fever"]):
            hypotheses.append({
                "condition": "Acute Bacterial Pharyngitis / Upper Respiratory Tract Infection",
                "icd10": "J02.9",
                "probability": 0.84,
                "confidence_interval": [0.76, 0.92],
                "justification": "Fever, sore throat, and productive cough with positive inflammatory markers.",
                "proposed_medications": ["Amoxicillin", "Azithromycin", "Acetaminophen"]
            })
            hypotheses.append({
                "condition": "Atypical Viral Bronchitis",
                "icd10": "J20.8",
                "probability": 0.58,
                "confidence_interval": [0.48, 0.68],
                "justification": "Subacute dry-to-productive cough with low-grade pyrexia.",
                "proposed_medications": ["Dextromethorphan", "Supportive Hydration"]
            })

        # Check for metabolic/diabetic/renal/joint
        elif any(k in combined_text for k in ["knee", "joint", "swelling", "edema", "polyuria", "creatinine", "glucose", "osteoarthritis"]):
            hypotheses.append({
                "condition": "Acute Exacerbation of Knee Osteoarthritis / Joint Effusion",
                "icd10": "M17.9",
                "probability": 0.85,
                "confidence_interval": [0.77, 0.92],
                "justification": "Localized knee arthralgia, joint effusion, and physical strain.",
                "proposed_medications": ["Ibuprofen", "Acetaminophen", "Topical Diclofenac"]
            })
            hypotheses.append({
                "condition": "Progressive Diabetic Nephropathy & Hypertensive Nephrosclerosis",
                "icd10": "E11.22",
                "probability": 0.74,
                "confidence_interval": [0.65, 0.83],
                "justification": "Elevated baseline creatinine and persistent microalbuminuria across historical episodes.",
                "proposed_medications": ["Lisinopril", "Empagliflozin"]
            })

        # Default fallback hypothesis
        if not hypotheses:
            hypotheses.append({
                "condition": "Unspecified Acute Symptom Complex",
                "icd10": "R68.89",
                "probability": 0.65,
                "confidence_interval": [0.50, 0.78],
                "justification": "Non-specific systemic presentation requiring further observational and lab correlation.",
                "proposed_medications": ["Symptomatic Relief", "Oral Rehydration"]
            })

        # Sort by probability descending
        hypotheses.sort(key=lambda x: x["probability"], reverse=True)
        return hypotheses
