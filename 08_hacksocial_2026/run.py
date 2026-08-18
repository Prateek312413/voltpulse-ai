"""
ResilioNet AI - Unified CLI & Web Server Launcher
Built for HackSocial 2026 Hackathon (Devpost)
"""

import os
import sys
import argparse
import webbrowser
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Launch ResilioNet AI Disaster Resilience Operations Grid")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark suite and exit")
    parser.add_argument("--test-mode", action="store_true", help="Run self-diagnostic verification and exit")
    args = parser.parse_args()

    # Benchmark mode
    if args.benchmark:
        from benchmark import run_all_benchmarks
        run_all_benchmarks()
        return

    # Diagnostic test mode
    if args.test_mode:
        import pytest
        code = pytest.main(["tests/", "-v"])
        sys.exit(code)

    # Ensure dataset exists
    feed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "synthetic_crisis_feed.json")
    if not os.path.exists(feed_path):
        from generate_crisis_data import generate_dataset
        generate_dataset()

    url = f"http://{args.host}:{args.port}"
    print("\n" + "=" * 70)
    print("  * RESILIONET AI - CRISIS OPERATIONS & MUTUAL-AID GRID *")
    print("  Edition: HackSocial 2026 (Devpost)")
    print("  Tracks:  AI/ML Track | Visual Design Track | Social Good")
    print("=" * 70)
    print(f"  [+] Web Operations Center: {url}")
    print(f"  [+] Interactive API Docs:   {url}/docs")
    print(f"  [+] REST Health Check:      {url}/health")
    print("=" * 70 + "\n")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run("main:app", host=args.host, port=args.port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
