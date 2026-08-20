"""
One-Click Zero-Config Auto-Browser Launcher for VoltPulse AI SCADA Operations Console.
"""

import uvicorn
import webbrowser
import threading
import time
import socket
import sys
import os

# Add local path to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def find_free_port(start_port: int = 8000) -> int:
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port


def open_browser(port: int):
    time.sleep(1.5)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[⚡ VoltPulse AI] Launching SCADA Dashboard in browser: {url}\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not auto-open browser: {e}")


def main():
    port = find_free_port(8000)
    print("=" * 75)
    print("  ⚡ VOLTPULSE AI: EDGE-AI BATTERY SCADA & RESILIENCE PLATFORM")
    print("  🏆 Official Submission for VoltHacks 2026 Hackathon (Devpost)")
    print(f"  📡 Server running at: http://127.0.0.1:{port}")
    print(f"  📚 Interactive API Docs: http://127.0.0.1:{port}/docs")
    print("=" * 75)

    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
