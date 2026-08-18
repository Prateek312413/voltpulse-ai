"""
AegisMed One-Click Launcher & Diagnostics
Automatically opens Clinician Console in browser.
"""

import sys
import time
import threading
import webbrowser
import uvicorn
import argparse
import logging
from aegismed.config import settings
from aegismed.database.connection import init_db, active_backend
from aegismed.database.seed_data import seed_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aegismed.launcher")


def auto_open_browser(port: int):
    """Waits for server initialization then launches default web browser."""
    time.sleep(1.2)
    url = f"http://localhost:{port}"
    logger.info(f"Opening Clinician Console in browser: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning(f"Could not open browser automatically: {e}")


def main():
    parser = argparse.ArgumentParser(description="AegisMed Clinical Agentic Memory Engine")
    parser.add_argument("--host", default=settings.HOST, help="Host to bind server")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind server")
    parser.add_argument("--seed", action="store_true", help="Re-seed benchmark clinical data")
    parser.add_argument("--no-browser", action="store_true", help="Disable automatic browser opening")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("   🏥 AEGISMED: CLINICAL AGENTIC MEMORY ENGINE")
    print("   CockroachDB × AWS Hackathon — Enterprise Clinical Intelligence")
    print("=" * 65)

    # Initialize Database & Seed
    init_db()
    seed_all()

    print(f"\n[✔] Database Memory Engine: Ready ({active_backend})")
    print(f"[✔] Multi-Agent Clinical Swarm: Online")
    print(f"[✔] Clinician Console: http://localhost:{args.port}\n" + "=" * 65 + "\n")

    # Auto-open browser in background thread
    if not args.no_browser:
        threading.Thread(target=auto_open_browser, args=(args.port,), daemon=True).start()

    uvicorn.run("aegismed.main:app", host=args.host, port=args.port, reload=False, log_level="warning")


if __name__ == "__main__":
    main()

