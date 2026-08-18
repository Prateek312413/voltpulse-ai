"""
Tests for CockroachDB Agent Skills Registry and Execution
"""

import pytest
from aegismed.skills import skill_registry


def test_skill_registry_loading():
    skills = skill_registry.list_skills()
    assert len(skills) >= 1
    skill_names = [s.get("name") for s in skills]
    assert "cockroach_clinical_memory_skill" in skill_names


def test_clinical_memory_skill_capabilities():
    skill = skill_registry.get_skill("cockroach_clinical_memory_skill")
    assert skill is not None
    caps = [c["name"] for c in skill.get("capabilities", [])]
    assert "episodic_vector_search" in caps
    assert "acquire_session_lock" in caps
    assert "reconcile_delayed_telemetry" in caps
