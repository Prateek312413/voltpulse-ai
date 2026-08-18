"""
ResilioNet AI - Synthetic Crisis Scenario Generator & Data Seed Script
Generates realistic multi-modal disaster signals, supply depots, and zone baselines.
"""

import json
import os
import random
import time
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "synthetic_crisis_feed.json")

SAMPLE_MESSAGES = [
    {
        "text": "EMERGENCY: Water rising past 2nd floor window! Family of 5 trapped including 1 newborn baby and my 78yo mother with diabetes. Insulin ruined. Location: 1420 Riverfront Ave, Sector 4. Coordinates: 37.7749, -122.4194. Please send boat and medical supplies!",
        "zone": "ZONE-COASTAL-4",
        "category_hint": "TRAPPED_SEARCH_RESCUE",
        "req_items": {"insulin_cold_pack": 2, "potable_water": 10, "infant_formula_diapers": 1, "trauma_first_aid_kit": 1}
    },
    {
        "text": "Elderly retirement center without power for 18 hours. 12 residents on oxygen concentrators. Generator fuel is down to 5%. Urgent diesel delivery or battery banks needed at 880 Highland Ridge Road (37.7833, -122.4167).",
        "zone": "ZONE-HIGHLAND-2",
        "category_hint": "POWER_INFRASTRUCTURE",
        "req_items": {"portable_generator_fuel": 4, "oxygen_concentrator": 3, "potable_water": 20}
    },
    {
        "text": "Roof collapsed during tremor! 3 construction workers trapped under concrete debris. One has severe arterial bleeding from leg fracture. Need immediate heavy search and rescue + trauma tourniquet at 505 Warehouse Row (37.7650, -122.4250).",
        "zone": "ZONE-INDUSTRIAL-1",
        "category_hint": "CRITICAL_MEDICAL",
        "req_items": {"trauma_first_aid_kit": 3, "potable_water": 5}
    },
    {
        "text": "Community shelter has taken in 45 flood evacuees. Completely out of clean drinking water and baby formula. 8 toddlers crying and dehydrated. Need potable water tanker and infant nutrition at Westside Community Gym (37.7550, -122.4350).",
        "zone": "ZONE-WESTSIDE-3",
        "category_hint": "WATER_FOOD_DEFICIT",
        "req_items": {"potable_water": 50, "infant_formula_diapers": 10, "mre_food_rations": 40}
    },
    {
        "text": "Extreme cold temperatures (-8C). Homeless shelter overflow, 30 people shivering under highway overpass at 12th & Market St. High hypothermia risk. Need thermal emergency blankets, hot rations, and winter sleeping bags (37.7720, -122.4150).",
        "zone": "ZONE-DOWNTOWN-1",
        "category_hint": "SHELTER_EXPOSURE",
        "req_items": {"thermal_blankets_tarp": 35, "mre_food_rations": 30, "potable_water": 15}
    },
    {
        "text": "Wildfire smoke index hazardous (AQI 450). Pediatric asthma clinic running out of albuterol inhalers and HEPA air purifiers. 6 children experiencing acute respiratory distress at East Health Center (37.7900, -122.4000).",
        "zone": "ZONE-EASTVALE-5",
        "category_hint": "CRITICAL_MEDICAL",
        "req_items": {"oxygen_concentrator": 6, "trauma_first_aid_kit": 2}
    },
    {
        "text": "SOS: We are 4 elderly neighbors cut off by mudslide on Mountain View Trail (37.8000, -122.4400). Single access road blocked by downed timber. Food and water exhausted. Phone battery at 4%.",
        "zone": "ZONE-MOUNTAIN-6",
        "category_hint": "TRAPPED_SEARCH_RESCUE",
        "req_items": {"mre_food_rations": 16, "potable_water": 12, "thermal_blankets_tarp": 4}
    },
    {
        "text": "Local clinic dialysis unit power failing. Need auxiliary fuel cell or backup battery pack for 8 patients awaiting treatment at Bayview Health Annex (37.7300, -122.3850).",
        "zone": "ZONE-BAYVIEW-7",
        "category_hint": "POWER_INFRASTRUCTURE",
        "req_items": {"portable_generator_fuel": 3, "potable_water": 10}
    }
]

SUPPLY_HUBS = [
    {
        "hub_id": "HUB-CENTRAL-01",
        "name": "Central Metro Emergency Logistics Warehouse",
        "latitude": 37.7700,
        "longitude": -122.4170,
        "capacity_units": 5000,
        "available_vehicles": 12,
        "operational_status": "ACTIVE",
        "inventory": {
            "potable_water": {"item_id": "WTR-01", "name": "Potable Water Gallons", "category": "WATER", "quantity": 300, "unit": "gallons", "is_perishable": False},
            "mre_food_rations": {"item_id": "MRE-01", "name": "Humanitarian MRE Rations", "category": "FOOD", "quantity": 250, "unit": "packs", "is_perishable": False},
            "trauma_first_aid_kit": {"item_id": "MED-01", "name": "Trauma First Aid Kits", "category": "MEDICAL", "quantity": 60, "unit": "kits", "is_perishable": False},
            "insulin_cold_pack": {"item_id": "MED-02", "name": "Refrigerated Rapid Insulin", "category": "MEDICAL", "quantity": 25, "unit": "vials", "is_perishable": True, "cold_chain_required": True},
            "oxygen_concentrator": {"item_id": "MED-03", "name": "Portable Oxygen Concentrators", "category": "MEDICAL", "quantity": 15, "unit": "units", "is_perishable": False},
            "infant_formula_diapers": {"item_id": "PEDIATRIC-01", "name": "Infant Formula & Diapers Bundle", "category": "PEDIATRIC", "quantity": 40, "unit": "kits", "is_perishable": True},
            "thermal_blankets_tarp": {"item_id": "SHELTER-01", "name": "Mylar Thermal Blankets & Tarps", "category": "SHELTER", "quantity": 180, "unit": "units", "is_perishable": False},
            "portable_generator_fuel": {"item_id": "POWER-01", "name": "Diesel Fuel Cans (5 Gallon)", "category": "POWER", "quantity": 30, "unit": "cans", "is_perishable": False}
        }
    },
    {
        "hub_id": "HUB-NORTH-02",
        "name": "North Harbor Red Cross Mutual-Aid Depot",
        "latitude": 37.7950,
        "longitude": -122.4100,
        "capacity_units": 2500,
        "available_vehicles": 6,
        "operational_status": "ACTIVE",
        "inventory": {
            "potable_water": {"item_id": "WTR-01", "name": "Potable Water Gallons", "category": "WATER", "quantity": 150, "unit": "gallons", "is_perishable": False},
            "mre_food_rations": {"item_id": "MRE-01", "name": "Humanitarian MRE Rations", "category": "FOOD", "quantity": 120, "unit": "packs", "is_perishable": False},
            "trauma_first_aid_kit": {"item_id": "MED-01", "name": "Trauma First Aid Kits", "category": "MEDICAL", "quantity": 30, "unit": "kits", "is_perishable": False},
            "thermal_blankets_tarp": {"item_id": "SHELTER-01", "name": "Mylar Thermal Blankets & Tarps", "category": "SHELTER", "quantity": 90, "unit": "units", "is_perishable": False},
            "portable_generator_fuel": {"item_id": "POWER-01", "name": "Diesel Fuel Cans (5 Gallon)", "category": "POWER", "quantity": 12, "unit": "cans", "is_perishable": False}
        }
    },
    {
        "hub_id": "HUB-SOUTH-03",
        "name": "South Bay Civic Resilience Staging Grounds",
        "latitude": 37.7400,
        "longitude": -122.4000,
        "capacity_units": 3000,
        "available_vehicles": 8,
        "operational_status": "ACTIVE",
        "inventory": {
            "potable_water": {"item_id": "WTR-01", "name": "Potable Water Gallons", "category": "WATER", "quantity": 200, "unit": "gallons", "is_perishable": False},
            "mre_food_rations": {"item_id": "MRE-01", "name": "Humanitarian MRE Rations", "category": "FOOD", "quantity": 180, "unit": "packs", "is_perishable": False},
            "trauma_first_aid_kit": {"item_id": "MED-01", "name": "Trauma First Aid Kits", "category": "MEDICAL", "quantity": 40, "unit": "kits", "is_perishable": False},
            "insulin_cold_pack": {"item_id": "MED-02", "name": "Refrigerated Rapid Insulin", "category": "MEDICAL", "quantity": 15, "unit": "vials", "is_perishable": True, "cold_chain_required": True},
            "oxygen_concentrator": {"item_id": "MED-03", "name": "Portable Oxygen Concentrators", "category": "MEDICAL", "quantity": 10, "unit": "units", "is_perishable": False},
            "infant_formula_diapers": {"item_id": "PEDIATRIC-01", "name": "Infant Formula & Diapers Bundle", "category": "PEDIATRIC", "quantity": 25, "unit": "kits", "is_perishable": True}
        }
    }
]

ZONE_PROFILES = [
    {
        "zone_id": "ZONE-COASTAL-4",
        "zone_name": "Lower Marina & Coastal District",
        "demographics": {"total_population": 28000, "elderly_ratio": 0.24, "infant_ratio": 0.11, "poverty_ratio": 0.22, "chronic_illness_ratio": 0.18},
        "infra": {"hospital_transit_minutes": 28.0, "grid_reliability_score": 0.35, "single_access_road_risk": True, "clean_water_access_score": 0.40, "cellular_coverage_pct": 0.60},
        "hazard": {"flood_water_level_meters": 1.8, "wildfire_proximity_km": None, "power_outage_active": True, "ambient_temp_celsius": 12.0, "roads_blocked_count": 4}
    },
    {
        "zone_id": "ZONE-HIGHLAND-2",
        "zone_name": "Highland Ridge Senior Enclave",
        "demographics": {"total_population": 14000, "elderly_ratio": 0.42, "infant_ratio": 0.04, "poverty_ratio": 0.12, "chronic_illness_ratio": 0.28},
        "infra": {"hospital_transit_minutes": 35.0, "grid_reliability_score": 0.40, "single_access_road_risk": True, "clean_water_access_score": 0.75, "cellular_coverage_pct": 0.70},
        "hazard": {"flood_water_level_meters": 0.0, "wildfire_proximity_km": 6.5, "power_outage_active": True, "ambient_temp_celsius": 29.0, "roads_blocked_count": 2}
    },
    {
        "zone_id": "ZONE-WESTSIDE-3",
        "zone_name": "Westside Community & School District",
        "demographics": {"total_population": 45000, "elderly_ratio": 0.14, "infant_ratio": 0.16, "poverty_ratio": 0.28, "chronic_illness_ratio": 0.14},
        "infra": {"hospital_transit_minutes": 18.0, "grid_reliability_score": 0.60, "single_access_road_risk": False, "clean_water_access_score": 0.55, "cellular_coverage_pct": 0.85},
        "hazard": {"flood_water_level_meters": 0.8, "wildfire_proximity_km": None, "power_outage_active": False, "ambient_temp_celsius": 14.0, "roads_blocked_count": 1}
    },
    {
        "zone_id": "ZONE-DOWNTOWN-1",
        "zone_name": "Downtown Civic Core & Transit Plaza",
        "demographics": {"total_population": 65000, "elderly_ratio": 0.12, "infant_ratio": 0.06, "poverty_ratio": 0.31, "chronic_illness_ratio": 0.16},
        "infra": {"hospital_transit_minutes": 8.0, "grid_reliability_score": 0.75, "single_access_road_risk": False, "clean_water_access_score": 0.80, "cellular_coverage_pct": 0.92},
        "hazard": {"flood_water_level_meters": 0.3, "wildfire_proximity_km": None, "power_outage_active": False, "ambient_temp_celsius": 8.0, "roads_blocked_count": 1}
    },
    {
        "zone_id": "ZONE-MOUNTAIN-6",
        "zone_name": "Mount Tamalpais Rural Foothills",
        "demographics": {"total_population": 6200, "elderly_ratio": 0.30, "infant_ratio": 0.05, "poverty_ratio": 0.09, "chronic_illness_ratio": 0.15},
        "infra": {"hospital_transit_minutes": 55.0, "grid_reliability_score": 0.20, "single_access_road_risk": True, "clean_water_access_score": 0.50, "cellular_coverage_pct": 0.35},
        "hazard": {"flood_water_level_meters": 0.0, "wildfire_proximity_km": 3.8, "power_outage_active": True, "ambient_temp_celsius": 32.0, "roads_blocked_count": 3}
    }
]


def generate_dataset(num_additional_sos: int = 12) -> Dict[str, Any]:
    os.makedirs(DATA_DIR, exist_ok=True)

    feed: List[Dict[str, Any]] = []
    # Include base realistic messages
    for i, item in enumerate(SAMPLE_MESSAGES):
        feed.append({
            "request_id": f"REQ-{i+1:04d}",
            "raw_text": item["text"],
            "zone_id": item["zone"],
            "category_hint": item["category_hint"],
            "required_items": item["req_items"],
            "timestamp_created": time.time() - (i * 300)
        })

    # Generate additional stochastic SOS distress signals
    streets = ["Oakland Blvd", "Mission St", "Pine Ridge Way", "Sunset Ave", "Elm St", "Harbor View Dr", "Valley Rd"]
    for j in range(num_additional_sos):
        idx = len(feed) + 1
        zone_choice = random.choice(ZONE_PROFILES)
        people = random.randint(1, 8)
        infants = 1 if (random.random() < 0.35 and people > 1) else 0
        elderly = 1 if (random.random() < 0.40 and people > 1) else 0
        street = random.choice(streets)
        num = random.randint(100, 9900)

        # Build realistic random text
        distress_types = [
            f"URGENT: Flooding reached {random.randint(1, 4)} ft inside home at {num} {street}. {people} family members trapped. No water for 24h.",
            f"Need medical aid immediately at {num} {street}. Grandmother suffering heart palpitations and severe dehydration. Headcount {people}.",
            f"Power down and freezing cold at {num} {street}. {people} people including {elderly} senior shivering. Need blankets and food rations.",
            f"We have {people} people stuck without food or clean water after storm blocked {street} near #{num}."
        ]
        chosen_text = random.choice(distress_types)

        req_items = {
            "potable_water": max(2, people * 2),
            "mre_food_rations": max(2, people * 3)
        }
        if infants > 0:
            req_items["infant_formula_diapers"] = infants * 2
        if elderly > 0:
            req_items["trauma_first_aid_kit"] = 1

        feed.append({
            "request_id": f"REQ-{idx:04d}",
            "raw_text": chosen_text,
            "zone_id": zone_choice["zone_id"],
            "category_hint": "AUTO_INGESTED",
            "required_items": req_items,
            "timestamp_created": time.time() - random.randint(60, 7200)
        })

    dataset = {
        "metadata": {
            "project": "ResilioNet AI",
            "hackathon": "HackSocial 2026",
            "generated_at": time.time(),
            "total_sos_signals": len(feed),
            "total_depots": len(SUPPLY_HUBS),
            "total_zones": len(ZONE_PROFILES)
        },
        "supply_hubs": SUPPLY_HUBS,
        "zone_profiles": ZONE_PROFILES,
        "distress_feed": feed
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"[OK] Generated synthetic crisis feed with {len(feed)} SOS requests, {len(SUPPLY_HUBS)} depots, and {len(ZONE_PROFILES)} zones at {OUTPUT_PATH}")
    return dataset


if __name__ == "__main__":
    generate_dataset()
