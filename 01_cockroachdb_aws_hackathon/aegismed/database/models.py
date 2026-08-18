"""
AegisMed Database Models
Defines CockroachDB & PostgreSQL compatible tables for:
- Patients
- Episodic Clinical Encounters (with Vector Embeddings)
- Working Memory Sessions (with ACID Locks)
- Semantic Medical Guidelines
- Reflective Meta-Insights
- Agent Audit Trails
"""

import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean, JSON, Index, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Patient(Base):
    """Core Patient Demographic & Health Identity"""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_uid = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(16), nullable=False)
    blood_type = Column(String(8), nullable=True)
    allergies = Column(JSON, default=list)  # List of known allergies e.g. ["Penicillin", "Sulfa"]
    chronic_conditions = Column(JSON, default=list)  # e.g. ["Type 2 Diabetes", "Hypertension"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    episodes = relationship("ClinicalEpisode", back_populates="patient", cascade="all, delete-orphan")
    insights = relationship("ReflectiveInsight", back_populates="patient", cascade="all, delete-orphan")
    sessions = relationship("WorkingMemorySession", back_populates="patient", cascade="all, delete-orphan")


class ClinicalEpisode(Base):
    """
    Tier 2: Episodic Memory
    Stores chronological patient encounters, doctor notes, labs, and high-dimensional vector embeddings.
    """
    __tablename__ = "clinical_episodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    episode_uid = Column(String(64), unique=True, index=True, nullable=False)
    patient_uid = Column(String(64), ForeignKey("patients.patient_uid"), nullable=False, index=True)
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    encounter_type = Column(String(64), default="OUTPATIENT_CONSULTATION") # INPATIENT, EMERGENCY, OUTPATIENT, LAB_REVIEW
    chief_complaint = Column(Text, nullable=False)
    symptoms = Column(JSON, default=list)
    vital_signs = Column(JSON, default=dict)  # {"bp_sys": 120, "bp_dia": 80, "hr": 72, "spo2": 98, "temp_c": 37.0}
    diagnosis = Column(String(256), nullable=True)
    icd10_code = Column(String(32), nullable=True)
    prescribed_medications = Column(JSON, default=list)  # [{"name": "Amoxicillin", "dose": "500mg", "freq": "TID"}]
    physician_notes = Column(Text, nullable=True)
    lab_results = Column(JSON, default=dict)  # {"creatinine": 1.1, "egfr": 75, "hba1c": 6.2}
    
    # Vector Embedding Storage (stored as JSON array for universal DB compatibility + vector queries)
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(64), default="amazon.titan-embed-text-v2:0")
    
    severity_score = Column(Float, default=1.0) # 1.0 (Low) to 5.0 (Critical)
    resolved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="episodes")


class WorkingMemorySession(Base):
    """
    Tier 1: Working Memory & State Management
    Provides ACID transaction guarantees and pessimistic/optimistic locking for multi-agent swarms.
    """
    __tablename__ = "working_memory_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    patient_uid = Column(String(64), ForeignKey("patients.patient_uid"), nullable=False, index=True)
    
    status = Column(String(32), default="ACTIVE") # ACTIVE, COMPLETED, FLAGGED, TERMINATED
    current_acuity = Column(String(32), default="STANDARD") # LOW, STANDARD, URGENT, RESUSCITATION
    active_agent = Column(String(64), default="TriageAgent")
    
    # Dynamic Agent Working State (Hypotheses, pending orders, intermediate findings)
    working_context = Column(JSON, default=dict)
    active_hypotheses = Column(JSON, default=list)
    pending_safety_checks = Column(JSON, default=list)
    agent_thoughts = Column(JSON, default=list)
    
    # Distributed Lock Management for Multi-Agent Consensus
    lock_owner = Column(String(64), nullable=True)
    lock_acquired_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1) # Optimistic concurrency control
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="sessions")


class SemanticGuideline(Base):
    """
    Tier 3: Semantic Medical Knowledge Base
    Stores clinical practice guidelines, contraindication rules, and drug interaction vectors.
    """
    __tablename__ = "semantic_guidelines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_uid = Column(String(64), unique=True, index=True, nullable=False)
    category = Column(String(64), index=True) # CONTRAINDICATION, DRUG_INTERACTION, CLINICAL_PROTOCOL
    
    title = Column(String(256), nullable=False)
    entity_a = Column(String(128), index=True) # e.g. "Penicillin" or "Chronic Kidney Disease"
    entity_b = Column(String(128), index=True) # e.g. "Amoxicillin" or "NSAIDs"
    risk_level = Column(String(32), default="HIGH") # WARNING, HIGH, CRITICAL, CONTRAINDICATED
    description = Column(Text, nullable=False)
    clinical_recommendation = Column(Text, nullable=False)
    source_authority = Column(String(128), default="FDA / WHO Clinical Guidelines")
    
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ReflectiveInsight(Base):
    """
    Tier 4: Reflective / Meta-Memory
    Autonomous agent reflection synthesizing patterns across longitudinal encounters.
    """
    __tablename__ = "reflective_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insight_uid = Column(String(64), unique=True, index=True, nullable=False)
    patient_uid = Column(String(64), ForeignKey("patients.patient_uid"), nullable=False, index=True)
    
    insight_type = Column(String(64), index=True) # ADVERSE_REACTION_PATTERN, DISEASE_PROGRESSION, THERAPEUTIC_RESISTANCE
    headline = Column(String(256), nullable=False)
    detailed_synthesis = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.90)
    source_episode_uids = Column(JSON, default=list)
    actionable_guidance = Column(Text, nullable=False)
    flagged_for_physician = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="insights")


class AgentAuditLog(Base):
    """
    Complete Traceability & Audit Trail
    Records exact memory queries, similarity scores, agent deliberation, and state transitions.
    """
    __tablename__ = "agent_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=True)
    patient_uid = Column(String(64), index=True, nullable=False)
    agent_name = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False) # WORKING_STATE_UPDATE, EPISODIC_SEARCH, SAFETY_ALERT, REFLECTION
    memory_tier = Column(String(32), nullable=False) # WORKING, EPISODIC, SEMANTIC, REFLECTIVE
    query_payload = Column(JSON, default=dict)
    result_summary = Column(Text, nullable=False)
    execution_time_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
