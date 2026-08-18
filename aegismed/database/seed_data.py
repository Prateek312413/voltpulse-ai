"""
AegisMed Seed Data & Benchmark Clinical Scenarios
Populates CockroachDB with realistic longitudinal patient histories,
semantic clinical guidelines, and high-impact medical safety benchmark cases.
"""

import datetime
import logging
from sqlalchemy.orm import Session
from aegismed.database.models import (
    Patient, ClinicalEpisode, SemanticGuideline, ReflectiveInsight
)
from aegismed.database.connection import get_db_session
from aegismed.memory.semantic_memory import SemanticMemoryManager
from aegismed.memory.episodic_memory import EpisodicMemoryManager

logger = logging.getLogger("aegismed.seed_data")


def seed_clinical_guidelines(db: Session):
    """Populates Tier-3 Semantic Medical Knowledge Base in CockroachDB."""
    sem_mgr = SemanticMemoryManager(db)
    
    guidelines = [
        {
            "category": "DRUG_ALLERGY_CONTRAINDICATION",
            "title": "Beta-Lactam Hypersensitivity in Penicillin-Allergic Patients",
            "entity_a": "Penicillin",
            "entity_b": "Amoxicillin",
            "risk_level": "CRITICAL",
            "description": "Patients with documented IgE-mediated or severe cutaneous adverse reactions to Penicillins share cross-reactivity with Aminopenicillins (Amoxicillin, Ampicillin).",
            "clinical_recommendation": "Avoid all beta-lactams. Substitute with Macrolides (Azithromycin, Clarithromycin) or Fluoroquinolones (Levofloxacin).",
            "source_authority": "FDA Clinical Drug Safety / WHO Guidelines"
        },
        {
            "category": "ORGAN_TOXICITY_CONTRAINDICATION",
            "title": "NSAID Nephrotoxicity in Renal Impairment & CKD",
            "entity_a": "Chronic Kidney Disease",
            "entity_b": "Ibuprofen",
            "risk_level": "CRITICAL",
            "description": "Non-steroidal anti-inflammatory drugs (NSAIDs) inhibit renal prostaglandin synthesis, causing acute reduction in renal blood flow and accelerating GFR loss in pre-existing CKD.",
            "clinical_recommendation": "Avoid systemic NSAIDs (Ibuprofen, Naproxen, Ketorolac). Use Acetaminophen or topical analgesics for pain control.",
            "source_authority": "KDIGO Clinical Practice Guideline for CKD"
        },
        {
            "category": "DRUG_INTERACTION",
            "title": "Statin and Macrolide Rhabdomyolysis Risk",
            "entity_a": "Atorvastatin",
            "entity_b": "Clarithromycin",
            "risk_level": "HIGH",
            "description": "Strong CYP3A4 inhibitors like Clarithromycin significantly increase systemic statin concentrations, escalating the risk of severe myopathy and rhabdomyolysis.",
            "clinical_recommendation": "Temporarily suspend statin therapy during macrolide antibiotic course or select Azithromycin (non-CYP3A4 inhibitor).",
            "source_authority": "American Heart Association (AHA) Drug Safety Advisory"
        },
        {
            "category": "CLINICAL_PROTOCOL",
            "title": "Acute Coronary Syndrome (ACS) Immediate Pharmacotherapy",
            "entity_a": "Chest Pain",
            "entity_b": "Aspirin",
            "risk_level": "STANDARD",
            "description": "Immediate administration of chewable non-enteric coated Aspirin (162-325 mg) and sublingual Nitroglycerin for acute ischemic chest discomfort.",
            "clinical_recommendation": "Administer STAT Aspirin 325mg chewable + Sublingual Nitroglycerin 0.4mg q5min x 3 doses if systolic BP > 90 mmHg.",
            "source_authority": "ACC/AHA Guideline for Management of Patients With Acute Coronary Syndromes"
        }
    ]

    for g in guidelines:
        existing = db.query(SemanticGuideline).filter(
            SemanticGuideline.title == g["title"]
        ).first()
        if not existing:
            sem_mgr.register_guideline(
                category=g["category"],
                title=g["title"],
                entity_a=g["entity_a"],
                entity_b=g["entity_b"],
                description=g["description"],
                clinical_recommendation=g["clinical_recommendation"],
                risk_level=g["risk_level"],
                source_authority=g["source_authority"]
            )
    logger.info("Successfully seeded Semantic Medical Knowledge in CockroachDB.")


def seed_benchmark_patients(db: Session):
    """Seeds multi-visit longitudinal patient profiles into CockroachDB."""
    epi_mgr = EpisodicMemoryManager(db)
    
    # --- PATIENT 1: Marcus Vance (Allergy Memory Test) ---
    p1 = db.query(Patient).filter(Patient.patient_uid == "P-1001").first()
    if not p1:
        p1 = Patient(
            patient_uid="P-1001",
            name="Marcus Vance",
            age=54,
            gender="Male",
            blood_type="O+",
            allergies=["Penicillin"],
            chronic_conditions=["Primary Hypertension"]
        )
        db.add(p1)
        db.commit()

        # Episode 1 (14 months ago): Dental infection + Anaphylaxis reaction
        epi_mgr.record_episode(
            patient_uid="P-1001",
            chief_complaint="Severe widespread erythematous hives and facial angioedema after taking Amoxicillin for dental abscess.",
            symptoms=["Urticarial rash", "Facial swelling", "Pruritus", "Mild wheezing"],
            diagnosis="Acute Drug-Induced Hypersensitivity Reaction / Penicillin Class Allergy",
            prescribed_medications=[
                {"name": "Diphenhydramine", "dose": "50mg", "freq": "STAT IV"},
                {"name": "Prednisone", "dose": "40mg", "freq": "Daily taper"}
            ],
            vital_signs={"bp_sys": 135, "bp_dia": 85, "hr": 92, "spo2": 96, "temp_c": 37.1},
            physician_notes="Patient developed acute severe IgE-mediated allergic response within 45 mins of Amoxicillin 500mg. Confirmed Penicillin class allergy. Hard allergy entered.",
            encounter_type="EMERGENCY_VISIT",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=420),
            severity_score=4.0
        )

        # Episode 2 (6 months ago): Routine hypertension check
        epi_mgr.record_episode(
            patient_uid="P-1001",
            chief_complaint="Routine 6-month blood pressure follow-up and prescription refill.",
            symptoms=["No acute complaints"],
            diagnosis="Well-Controlled Essential Hypertension",
            prescribed_medications=[
                {"name": "Amlodipine", "dose": "5mg", "freq": "Once daily"}
            ],
            vital_signs={"bp_sys": 128, "bp_dia": 82, "hr": 70, "spo2": 99, "temp_c": 36.8},
            physician_notes="BP remains stable on Amlodipine monotherapy. Reminded of strict Penicillin allergy avoidance.",
            encounter_type="OUTPATIENT_CONSULTATION",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=180),
            severity_score=1.0
        )

    # --- PATIENT 2: Elena Rostova (Renal Progression & Reflection Test) ---
    p2 = db.query(Patient).filter(Patient.patient_uid == "P-1002").first()
    if not p2:
        p2 = Patient(
            patient_uid="P-1002",
            name="Elena Rostova",
            age=67,
            gender="Female",
            blood_type="A-",
            allergies=["Sulfa"],
            chronic_conditions=["Type 2 Diabetes Mellitus", "Stage 3 Chronic Kidney Disease"]
        )
        db.add(p2)
        db.commit()

        # Episode 1 (18 months ago): Baseline renal lab
        epi_mgr.record_episode(
            patient_uid="P-1002",
            chief_complaint="Annual diabetic comprehensive metabolic panel and microalbuminuria screening.",
            symptoms=["Mild bilateral pedal edema"],
            diagnosis="Type 2 Diabetes Mellitus with Early Diabetic Nephropathy",
            prescribed_medications=[{"name": "Metformin", "dose": "500mg", "freq": "BID"}],
            vital_signs={"bp_sys": 138, "bp_dia": 86, "hr": 74, "spo2": 98, "temp_c": 36.7},
            lab_results={"creatinine": 1.05, "egfr": 68.0, "hba1c": 6.8},
            physician_notes="Baseline renal function borderline. Monitor eGFR every 6 months.",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=540),
            severity_score=1.5
        )

        # Episode 2 (6 months ago): Renal decline noted
        epi_mgr.record_episode(
            patient_uid="P-1002",
            chief_complaint="Follow-up for worsening fatigue and persistent ankle swelling.",
            symptoms=["Fatigue", "Bilateral pedal edema 2+"],
            diagnosis="Diabetic Kidney Disease Stage 3a (Down-trending eGFR)",
            prescribed_medications=[{"name": "Linagliptin", "dose": "5mg", "freq": "Daily"}],
            vital_signs={"bp_sys": 142, "bp_dia": 88, "hr": 78, "spo2": 97, "temp_c": 36.9},
            lab_results={"creatinine": 1.45, "egfr": 46.0, "hba1c": 7.4},
            physician_notes="Creatinine rose from 1.05 to 1.45 mg/dL. Strict avoidance of all nephrotoxic agents and NSAIDs.",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=180),
            severity_score=2.5
        )

    # --- PATIENT 3: David Chen (Acute Cardiopulmonary Case) ---
    p3 = db.query(Patient).filter(Patient.patient_uid == "P-1003").first()
    if not p3:
        p3 = Patient(
            patient_uid="P-1003",
            name="David Chen",
            age=61,
            gender="Male",
            blood_type="B+",
            allergies=[],
            chronic_conditions=["Hyperlipidemia", "Coronary Artery Disease"]
        )
        db.add(p3)
        db.commit()

        epi_mgr.record_episode(
            patient_uid="P-1003",
            chief_complaint="Exertional chest tightness during stair climbing, relieved by rest.",
            symptoms=["Exertional dyspnea", "Mild substernal pressure"],
            diagnosis="Stable Angina Pectoris",
            prescribed_medications=[
                {"name": "Atorvastatin", "dose": "40mg", "freq": "Nightly"},
                {"name": "Metoprolol Succinate", "dose": "25mg", "freq": "Daily"}
            ],
            vital_signs={"bp_sys": 140, "bp_dia": 90, "hr": 82, "spo2": 98, "temp_c": 36.8},
            physician_notes="Stress test positive for inducible ischemia. Initiated cardioprotective pharmacotherapy.",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=90),
            severity_score=2.0
        )

    logger.info("Successfully seeded benchmark patient profiles into CockroachDB.")


def seed_all():
    """Initializes and seeds the entire database."""
    with get_db_session() as db:
        seed_clinical_guidelines(db)
        seed_benchmark_patients(db)
