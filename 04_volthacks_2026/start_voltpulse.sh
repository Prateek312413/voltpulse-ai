#!/usr/bin/env bash
set -e
echo "==========================================================================="
echo "  VOLTPULSE AI: EDGE-AI BATTERY SCADA & RESILIENCE PLATFORM"
echo "  VoltHacks 2026 1-Click Zero-Config Launcher"
echo "==========================================================================="
cd "$(dirname "$0")"
pip install -r requirements.txt
python run.py
