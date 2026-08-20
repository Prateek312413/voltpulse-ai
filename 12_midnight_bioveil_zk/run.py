#!/usr/bin/env python3
"""
BioVeil ZK — Unified Protocol Launcher
Zero-Knowledge Clinical Trial & Genomic Intelligence on Midnight Blockchain
Brainwave 2026 Midnight Track
"""

import sys
import os
import webbrowser
import time
import uvicorn

# Ensure repository root is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

def print_banner():
    banner = r"""
==============================================================================
   ____  _       _    __      _  __     _______  __
  / __ )(_)___  | |  / /___  (_)/ /    /__  / // /__
 / __  / / __ \ | | / // _ \/ // /       / / // ,<   
/ /_/ / / /_/ / | |/ //  __/ // /       / /_/ // /| | 
\____/_/\____/  |___/ \___/_//_/       /____//_/ |_|  
                                                      
 Zero-Knowledge Clinical Trial & Genomic Intelligence Protocol
 Built for Brainwave 2026 – Midnight Track (Devpost)
 Powered by Midnight Blockchain & Compact Smart Contracts
==============================================================================
    """
    print(banner)

def main():
    print_banner()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"[*] Initializing Midnight Network Prover & Dual-State Ledger...")
    print(f"[*] Loading Compact Smart Contracts (BioVeilZK, ShieldEscrow, AuditCompliance)...")
    print(f"[*] Server starting on http://{host}:{port}")
    print(f"[*] Opening browser automatically in 1.5 seconds...\n")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://{host}:{port}")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
