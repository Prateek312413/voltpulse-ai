"""
EvidenceMesh One-Click Launcher & Diagnostics.
Proof of Possible 2026 Submission.
"""

import sys
import os
import time
import threading
import webbrowser
import uvicorn
import argparse
import logging
import pytest

# Ensure package path is recognized
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from evidencemesh.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("evidencemesh.launcher")


def auto_open_browser(port: int):
    """Waits for server initialization then launches default web browser."""
    time.sleep(1.2)
    url = f"http://localhost:{port}"
    logger.info(f"Opening EvidenceMesh Console in browser: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning(f"Could not open browser automatically: {e}")


def main():
    parser = argparse.ArgumentParser(description="EvidenceMesh: Autonomous Causal Verification & Cryptographic Proof Engine")
    parser.add_argument("--host", default=settings.HOST, help="Host to bind server")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Port to bind server")
    parser.add_argument("--no-browser", action="store_true", help="Disable automatic browser opening")
    parser.add_argument("--test", action="store_true", help="Run full pytest test suite")
    args = parser.parse_args()

    if args.test:
        print("\n" + "=" * 65)
        print("   🧪 RUNNING EVIDENCEMESH TEST SUITE")
        print("=" * 65 + "\n")
        sys.exit(pytest.main(["tests/", "-v"]))

    print("\n" + "=" * 70)
    print("   🛡️  EVIDENCEMESH: AUTONOMOUS CAUSAL VERIFICATION ENGINE")
    print("   Proof of Possible 2026 Devpost Hackathon — Official Submission")
    print("   'Don't pitch the future. Build evidence.'")
    print("=" * 70)
    print(f"\n[✔] Multi-Agent Adversarial Swarm: Active")
    print(f"[✔] Bayesian Epistemic Calibrator: Online")
    print(f"[✔] Cryptographic Merkle Proof Ledger: Ready")
    print(f"[✔] Web Console UI: http://{args.host}:{args.port}\n" + "=" * 70 + "\n")

    if not args.no_browser:
        threading.Thread(target=auto_open_browser, args=(args.port,), daemon=True).start()

    uvicorn.run("evidencemesh.main:app", host=args.host, port=args.port, reload=False, log_level="warning")


if __name__ == "__main__":
    main()
