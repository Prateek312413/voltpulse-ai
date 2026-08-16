"""
Physics-Informed Synthetic Battery Telemetry Generator.
Simulates realistic Li-ion battery capacity fade, SEI layer growth,
impedance rise, and thermal fluctuations across hundreds of charge-discharge cycles.
"""

from datetime import datetime, timedelta, timezone
import numpy as np
from typing import List, Dict, Any, Optional


def generate_battery_telemetry(
    battery_id: str,
    num_cycles: int = 150,
    nominal_capacity: float = 2.0,
    initial_soh: float = 1.0,
    degradation_rate: float = 0.0012,
    noise_level: float = 0.003,
    start_time: Optional[datetime] = None,
    drop_cycles: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Generates a realistic sequence of battery observations:
    - SOH(t) = SOH_0 - a * sqrt(cycle) - b * cycle + noise (SEI film + linear fade)
    - Voltage curve reflects average discharge plateau (3.7V - 3.4V)
    - Cell temperature models cycling heat dissipation (25°C to 38°C)
    """
    start = start_time or (datetime.now(timezone.utc) - timedelta(days=num_cycles))
    observations = []
    drop_set = set(drop_cycles or [])

    current_soh = initial_soh
    np.random.seed(hash(battery_id) % (2**31 - 1))

    for c in range(1, num_cycles + 1):
        if c in drop_set:
            continue

        # Physical degradation equation: SEI root-time growth + linear wear
        sei_fade = 0.0035 * np.sqrt(c / 10.0)
        linear_fade = degradation_rate * c
        thermal_noise = float(np.random.normal(0.0, noise_level))
        
        soh = max(0.60, min(1.05, initial_soh - (sei_fade + linear_fade) + thermal_noise))
        capacity = max(0.5, nominal_capacity * soh)
        
        # Sensor readings
        voltage = round(float(3.75 - 0.35 * (1.0 - soh) + np.random.normal(0, 0.02)), 3)
        current = round(float(1.50 + np.random.normal(0, 0.05)), 2)
        temperature = round(float(28.0 + 8.0 * (1.0 - soh) + np.random.normal(0, 1.2)), 1)
        
        rec_time = start + timedelta(hours=4 * c)

        obs = {
            "observation_id": f"OBS-{battery_id}-C{c:03d}",
            "battery_id": battery_id,
            "cycle_number": c,
            "recorded_at": rec_time.isoformat(),
            "voltage": voltage,
            "current": current,
            "temperature": temperature,
            "capacity": round(float(capacity), 3),
            "soh": round(float(soh), 4)
        }
        observations.append(obs)

    return observations
