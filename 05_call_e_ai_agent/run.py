#!/usr/bin/env python3
"""
ProcurePulse AI - Application Runner
Launches the FastAPI server and serves the Procurement Workbench dashboard.
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Setup Paths
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "apps" / "procure-pulse-workbench"
SKILLS_DIR = PROJECT_ROOT / "skills" / "procure-pulse-negotiator"

for p in [PROJECT_ROOT, BACKEND_DIR, SKILLS_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import uvicorn
from backend.database import init_db


def main():
    print("=" * 70)
    print("  ☎️  ProcurePulse AI — Autonomous Supplier RFQ & Negotiation Voice Engine")
    print("  🏆 Devpost CALL-E Hackathon Submission Package")
    print("=" * 70)
    
    # Initialize database
    init_db()
    print("[1/2] SQLite Database initialized & seeded with industrial suppliers.")
    print("[2/2] Starting ProcurePulse FastAPI Server on http://localhost:8000 ...")
    print("\n  👉 Open Workbench UI: http://localhost:8000")
    print("  👉 API Documentation: http://localhost:8000/docs")
    print("=" * 70)

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
