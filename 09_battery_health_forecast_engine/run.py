"""
CLI Launcher for Uncertainty-Aware Battery Health Forecast Engine.
Usage:
  python run.py              # Starts API backend & Web Interface on http://localhost:8000
  python run.py --test       # Runs full pytest test suite for all 12 edge cases
  python run.py --seed       # Seeds database with demo battery and NASA-style telemetry
  python run.py --benchmark  # Runs high-throughput GPR kernel benchmark suite
"""

import argparse
import sys
import webbrowser
import threading
import time
import uvicorn
import pytest

from app.database import init_db, SessionLocal
from app.models.battery import Battery
from app.models.telemetry import TelemetryObservation
from app.models.forecast import Forecast
from data.generator import generate_battery_telemetry
from app.core.temporal import build_active_temporal_dataset
from app.core.evaluator import evaluate_candidate_models
from app.core.forecaster import generate_forecast
from datetime import datetime, timezone
import json


def seed_database():
    """Seeds database with realistic demo battery degradation data."""
    init_db()
    db = SessionLocal()
    bat_id = "BAT-NASA-DEMO-01"

    print(f"[*] Seeding battery '{bat_id}'...")
    bat = db.query(Battery).filter(Battery.id == bat_id).first()
    if not bat:
        bat = Battery(id=bat_id, battery_type="Li-ion NMC (18650)", nominal_capacity=2.0, active_telemetry_version=1)
        db.add(bat)
        db.commit()

    raw_obs = generate_battery_telemetry(bat_id, num_cycles=80)
    for item in raw_obs:
        existing = db.query(TelemetryObservation).filter(
            TelemetryObservation.battery_id == bat_id,
            TelemetryObservation.observation_id == item["observation_id"]
        ).first()
        if not existing:
            obs = TelemetryObservation(
                id=f"OBS-{bat_id}-C{item['cycle_number']:03d}-v1",
                observation_id=item["observation_id"],
                battery_id=bat_id,
                cycle_number=item["cycle_number"],
                recorded_at=datetime.fromisoformat(item["recorded_at"]),
                received_at=datetime.now(timezone.utc),
                voltage=item["voltage"],
                current=item["current"],
                temperature=item["temperature"],
                capacity=item["capacity"],
                soh=item["soh"],
                is_active=True,
                version=1,
                telemetry_version=bat.active_telemetry_version
            )
            db.add(obs)
            bat.active_telemetry_version += 1
    db.commit()

    # Generate initial forecast at cycle 120
    obs_records = [o.to_dict() for o in db.query(TelemetryObservation).filter(TelemetryObservation.battery_id == bat_id).all()]
    _, cfg, X, y = build_active_temporal_dataset(obs_records)
    evals, best = evaluate_candidate_models(X, y)
    
    fc_res = generate_forecast(X, y, cfg, target_cycle=120, selected_kernel_name=best.kernel_type, telemetry_version=bat.active_telemetry_version)
    
    fc_id = f"FC-{bat_id}-C120-v1"
    existing_fc = db.query(Forecast).filter(Forecast.id == fc_id).first()
    if not existing_fc:
        fc = Forecast(
            id=fc_id,
            battery_id=bat_id,
            forecast_version=1,
            source_telemetry_version=bat.active_telemetry_version,
            target_cycle=120,
            predicted_soh=fc_res.predicted_soh,
            std_dev=fc_res.std_dev,
            lower_ci=fc_res.lower_ci,
            upper_ci=fc_res.upper_ci,
            selected_kernel=fc_res.selected_kernel,
            hyperparameters_json=json.dumps(fc_res.hyperparameters),
            jitter_used=fc_res.jitter_used,
            noise_variance=fc_res.noise_variance,
            multi_horizon_json=json.dumps(fc_res.multi_horizon_points)
        )
        db.add(fc)
        db.commit()

    db.close()
    print("[+] Database seeding complete! 80 cycles and initial forecast v1 ready.")


def open_browser(url: str):
    time.sleep(1.2)
    webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(description="Uncertainty-Aware Battery Health Forecast Engine")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--test", action="store_true", help="Run pytest automated test suite")
    parser.add_argument("--seed", action="store_true", help="Seed database with demo dataset")
    parser.add_argument("--benchmark", action="store_true", help="Run model benchmark suite")
    parser.add_argument("--no-browser", dest="no_browser", action="store_true", help="Do not automatically launch web browser")

    args = parser.parse_args()

    if args.test:
        print("[*] Running full automated test suite...")
        sys.exit(pytest.main(["tests/", "-v"]))

    if args.benchmark:
        print("[*] Running performance benchmark suite...")
        import subprocess
        sys.exit(subprocess.call([sys.executable, "benchmark.py"]))

    if args.seed:
        seed_database()
        return

    print("==========================================================================")
    print("  UNCERTAINTY-AWARE BATTERY HEALTH FORECAST ENGINE (GPR + RECONCILIATION)")
    print("==========================================================================")
    print(f"[*] Starting local server on http://{args.host}:{args.port}")
    print(f"[*] Interactive UI available at: http://{args.host}:{args.port}/")
    print(f"[*] Swagger API Docs available at: http://{args.host}:{args.port}/docs")
    print("==========================================================================")

    init_db()
    # Auto-seed if database is empty
    db = SessionLocal()
    if db.query(Battery).count() == 0:
        print("[*] Empty database detected. Auto-seeding NASA demo battery dataset...")
        db.close()
        seed_database()
    else:
        db.close()

    if not args.no_browser:
        threading.Thread(target=open_browser, args=(f"http://{args.host}:{args.port}",), daemon=True).start()

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
