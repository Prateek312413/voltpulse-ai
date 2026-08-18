"""
ResilioNet AI - Situational Awareness & Resilience Analytics Endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
try:
    from core.state import crisis_db
    from core.vulnerability_index import HyperlocalVulnerabilityIndex, RealtimeHazardModifiers
    from core.situational_agent import SituationalAssessment
except ImportError:
    from ..core.state import crisis_db
    from ..core.vulnerability_index import HyperlocalVulnerabilityIndex, RealtimeHazardModifiers
    from ..core.situational_agent import SituationalAssessment

router = APIRouter()


class HazardUpdateRequest(BaseModel):
    flood_water_level_meters: float = 0.0
    wildfire_proximity_km: Optional[float] = None
    power_outage_active: bool = False
    ambient_temp_celsius: float = 24.0
    roads_blocked_count: int = 0


@router.get("/dashboard_summary")
async def get_dashboard_summary():
    """Aggregates real-time top-level KPI telemetry for command dashboard."""
    plan = crisis_db.latest_plan or crisis_db.run_matching_cycle()
    total_sos = len(crisis_db.triage_records)
    critical_sos = sum(1 for t in crisis_db.triage_records.values() if t.urgency_score >= 8.5)
    high_urgency_sos = sum(1 for t in crisis_db.triage_records.values() if 6.5 <= t.urgency_score < 8.5)
    moderate_sos = total_sos - critical_sos - high_urgency_sos

    total_supplies = sum(
        sum(item.quantity for item in hub.inventory.values())
        for hub in crisis_db.supply_hubs.values()
    )

    active_depots = sum(1 for hub in crisis_db.supply_hubs.values() if hub.operational_status == "ACTIVE")
    offline_depots = sum(1 for hub in crisis_db.supply_hubs.values() if hub.operational_status == "OFFLINE")

    return {
        "total_active_sos": total_sos,
        "critical_life_safety_count": critical_sos,
        "high_urgency_count": high_urgency_sos,
        "moderate_count": moderate_sos,
        "matched_and_dispatched": plan.matched_demands,
        "fulfillment_rate_pct": plan.fulfillment_rate_percent,
        "gini_equity_index": plan.gini_equity_index,
        "total_supplies_in_stock": total_supplies,
        "active_depots": active_depots,
        "offline_depots": offline_depots,
        "total_monitored_zones": len(crisis_db.zone_profiles),
        "disaster_ledger_blocks": len(crisis_db.audit_ledger.chain)
    }


@router.get("/zones", response_model=List[HyperlocalVulnerabilityIndex])
async def list_zone_vulnerability_profiles():
    """Lists all monitored neighborhood zones with computed HRVI scores and hazard profiles."""
    return sorted(list(crisis_db.zone_profiles.values()), key=lambda z: z.composite_hrvi, reverse=True)


@router.get("/situational_assessment", response_model=SituationalAssessment)
async def get_ai_incident_commander_assessment():
    """Returns AI Incident Commander comprehensive situation report and actionable field directives."""
    return crisis_db.get_situational_assessment()


@router.post("/zone/{zone_id}/hazard_update", response_model=HyperlocalVulnerabilityIndex)
async def update_zone_hazard(zone_id: str, hazard: HazardUpdateRequest):
    """
    Simulates incoming environmental sensor telemetry (e.g. rising river, fire perimeter, grid outage)
    and dynamically re-computes HRVI risk tier.
    """
    if zone_id not in crisis_db.zone_profiles:
        raise HTTPException(status_code=404, detail=f"Zone ID '{zone_id}' not found")

    old_hrvi = crisis_db.zone_profiles[zone_id]

    # Recompute with new hazard data
    # Create default demo and infra fallback if not cached
    from ..core.vulnerability_index import ZoneDemographics, ZoneInfrastructure
    demo = ZoneDemographics(total_population=25000, elderly_ratio=0.25, infant_ratio=0.10, poverty_ratio=0.20, chronic_illness_ratio=0.15)
    infra = ZoneInfrastructure(hospital_transit_minutes=25.0, grid_reliability_score=0.4 if hazard.power_outage_active else 0.8)
    haz = RealtimeHazardModifiers(**hazard.model_dump())

    new_hrvi = crisis_db.vuln_profiler.compute_hrvi(zone_id, old_hrvi.zone_name, demo, infra, haz)
    crisis_db.zone_profiles[zone_id] = new_hrvi

    crisis_db.audit_ledger.append_event("ZONE_HAZARD_TELEMETRY_UPDATED", {
        "zone_id": zone_id,
        "old_hrvi": old_hrvi.composite_hrvi,
        "new_hrvi": new_hrvi.composite_hrvi,
        "risk_tier": new_hrvi.risk_tier
    })

    crisis_db.run_matching_cycle()
    return new_hrvi
