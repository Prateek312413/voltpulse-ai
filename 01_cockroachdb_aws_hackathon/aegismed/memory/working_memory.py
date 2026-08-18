"""
Tier 1: Working Memory Manager
Coordinates transient consultation state, working hypotheses, active triage,
and ACID lock arbitration between collaborating agents in CockroachDB.
"""

import time
import datetime
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from aegismed.database.models import WorkingMemorySession
from aegismed.memory.base import MemoryTier, MemoryNode

logger = logging.getLogger("aegismed.working_memory")


class WorkingMemoryManager:
    """Manages active session context and transactional state locks."""

    def __init__(self, db: Session):
        self.db = db

    def initialize_session(self, patient_uid: str, initial_data: Dict[str, Any] = None) -> WorkingMemorySession:
        """Initializes a new clinical consultation session in CockroachDB."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        new_session = WorkingMemorySession(
            session_id=session_id,
            patient_uid=patient_uid,
            status="ACTIVE",
            current_acuity="STANDARD",
            active_agent="TriageAgent",
            working_context=initial_data or {},
            active_hypotheses=[],
            pending_safety_checks=[],
            agent_thoughts=[],
            version=1
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        logger.info(f"Initialized Working Memory Session {session_id} for Patient {patient_uid}")
        return new_session

    def acquire_lock(self, session_id: str, agent_name: str) -> bool:
        """Pessimistic / Optimistic lock acquisition on active session state."""
        session = self.db.query(WorkingMemorySession).filter(
            WorkingMemorySession.session_id == session_id
        ).with_for_update().first()

        if not session:
            return False

        # If already locked by someone else within 10 seconds, return False
        now = datetime.datetime.utcnow()
        if session.lock_owner and session.lock_owner != agent_name:
            if session.lock_acquired_at and (now - session.lock_acquired_at).total_seconds() < 10:
                logger.warning(f"Lock contention: {agent_name} denied lock on {session_id}, owned by {session.lock_owner}")
                return False

        session.lock_owner = agent_name
        session.lock_acquired_at = now
        session.active_agent = agent_name
        session.version += 1
        self.db.commit()
        return True

    def release_lock(self, session_id: str, agent_name: str):
        """Releases the state lock."""
        session = self.db.query(WorkingMemorySession).filter(
            WorkingMemorySession.session_id == session_id
        ).first()
        if session and session.lock_owner == agent_name:
            session.lock_owner = None
            session.lock_acquired_at = None
            self.db.commit()

    def record_agent_thought(self, session_id: str, agent_name: str, thought_text: str, step_type: str = "REASONING"):
        """Appends real-time agent reasoning step into working session memory."""
        session = self.db.query(WorkingMemorySession).filter(
            WorkingMemorySession.session_id == session_id
        ).first()
        if session:
            thoughts = list(session.agent_thoughts or [])
            thoughts.append({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "agent": agent_name,
                "type": step_type,
                "content": thought_text
            })
            session.agent_thoughts = thoughts
            self.db.commit()

    def update_working_state(
        self,
        session_id: str,
        acuity: Optional[str] = None,
        hypotheses: Optional[List[Dict[str, Any]]] = None,
        safety_checks: Optional[List[Dict[str, Any]]] = None,
        context_updates: Optional[Dict[str, Any]] = None
    ):
        """Updates active working context in CockroachDB."""
        session = self.db.query(WorkingMemorySession).filter(
            WorkingMemorySession.session_id == session_id
        ).first()
        if session:
            if acuity:
                session.current_acuity = acuity
            if hypotheses is not None:
                session.active_hypotheses = hypotheses
            if safety_checks is not None:
                session.pending_safety_checks = safety_checks
            if context_updates:
                ctx = dict(session.working_context or {})
                ctx.update(context_updates)
                session.working_context = ctx
            
            session.version += 1
            self.db.commit()

    def get_session(self, session_id: str) -> Optional[WorkingMemorySession]:
        return self.db.query(WorkingMemorySession).filter(
            WorkingMemorySession.session_id == session_id
        ).first()
