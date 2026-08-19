@echo off
echo ===========================================================================
echo   VOLTPULSE AI: EDGE-AI BATTERY SCADA &amp; RESILIENCE PLATFORM
echo   VoltHacks 2026 1-Click Zero-Config Launcher
echo ===========================================================================
cd /d "%~dp0"
python -m pip install -r requirements.txt
python run.py
pause
