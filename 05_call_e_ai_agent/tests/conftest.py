"""
Pytest configuration for ProcurePulse AI.
Configures sys.path so all test modules can import backend, skills, and plugins cleanly.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "apps" / "procure-pulse-workbench"
SKILLS_DIR = ROOT_DIR / "skills" / "procure-pulse-negotiator"

for p in [ROOT_DIR, BACKEND_DIR, SKILLS_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
