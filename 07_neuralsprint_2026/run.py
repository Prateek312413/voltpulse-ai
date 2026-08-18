"""
NeuroAccess AI - Foolproof Launch Runner
Automatically handles port selection, socket verification, and browser guidance for Judges.
"""
import sys
import socket
import argparse
import webbrowser
import uvicorn
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def find_available_port(preferred_port=8000):
    """Finds an open port starting from preferred_port."""
    for port in [preferred_port, 8080, 8001, 8888, 5000]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return preferred_port

def main():
    parser = argparse.ArgumentParser(description="NeuroAccess AI Runner")
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    port = find_available_port(args.port)
    url = f"http://127.0.0.1:{port}"

    print("=" * 75)
    print(">> Starting NeuroAccess AI Assistive Core (NeuralSprint 2026)")
    print("=" * 75)
    print(f"   [1] Interactive Web UI:     {url}")
    print(f"   [2] Interactive API Docs:   {url}/docs")
    print(f"   [3] Real-time Health API:   {url}/api/health")
    print(f"   [4] One-Click Guided Demo:  {url} (Click 'Judge Quick Tour')")
    print("=" * 75)

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
