"""
CockroachDB Agent Skills Package
Loads and executes portable, machine-executable Agent Skills for schema design,
vector retrieval, lock arbitration, and observability.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aegismed.skills")


class AgentSkillRegistry:
    """Manages open-source CockroachDB Agent Skills."""

    def __init__(self):
        self.skills: Dict[str, Any] = {}
        self.skills_dir = os.path.dirname(__file__)
        self._load_skills()

    def _load_skills(self):
        """Loads all JSON skill manifests from skills directory."""
        if not os.path.exists(self.skills_dir):
            return
        for file in os.listdir(self.skills_dir):
            if file.endswith(".json"):
                path = os.path.join(self.skills_dir, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.skills[data.get("name", file)] = data
                        logger.info(f"Loaded CockroachDB Agent Skill: {data.get('name')}")
                except Exception as e:
                    logger.error(f"Failed to load skill from {file}: {e}")

    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        return self.skills.get(skill_name)

    def list_skills(self) -> List[Dict[str, Any]]:
        return list(self.skills.values())


skill_registry = AgentSkillRegistry()

__all__ = ["AgentSkillRegistry", "skill_registry"]
