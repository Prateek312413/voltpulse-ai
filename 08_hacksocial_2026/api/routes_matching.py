"""
ResilioNet AI - Resource Matching & Optimization Endpoints
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
try:
    from core.state import crisis_db
    from core.resource_optimizer import AllocationPlan, MatchResult
except ImportError:
    from ..core.state import crisis_db
    from ..core.resource_optimizer import AllocationPlan, MatchResult

router = APIRouter()


class ReoptimizeParams(BaseModel):
    fairness_weight: float = Field(0.35, ge=0.0, le=1.0)
    distance_penalty_weight: float = Field(0.05, ge=0.0, le=1.0)


@router.get("/latest_plan", response_model=AllocationPlan)
async def get_latest_allocation_plan():
    """Fetches current global resource allocation plan and equity metrics."""
    if not crisis_db.latest_plan:
        return crisis_db.run_matching_cycle()
    return crisis_db.latest_plan


@router.post("/reoptimize", response_model=AllocationPlan)
async def reoptimize_network(params: Optional[ReoptimizeParams] = None):
    """Recomputes global matching with updated mathematical weights."""
    if params:
        crisis_db.optimizer.fairness_weight = params.fairness_weight
        crisis_db.optimizer.distance_penalty_weight = params.distance_penalty_weight

    return crisis_db.run_matching_cycle()


@router.post("/dispatch/{match_id}")
async def dispatch_allocation_match(match_id: str, new_status: str = "DISPATCHED"):
    """Updates field dispatch status of a matched aid convoy (PENDING -> DISPATCHED -> DELIVERED)."""
    if not crisis_db.latest_plan:
        raise HTTPException(status_code=404, detail="No active allocation plan found")

    target_match = None
    for m in crisis_db.latest_plan.matches:
        if m.match_id == match_id:
            target_match = m
            m.dispatch_status = new_status
            break

    if not target_match:
        raise HTTPException(status_code=404, detail=f"Match ID '{match_id}' not found")

    crisis_db.audit_ledger.append_event("AID_DISPATCH_UPDATED", {
        "match_id": match_id,
        "request_id": target_match.request_id,
        "hub_id": target_match.hub_id,
        "status": new_status
    })

    return {"status": "SUCCESS", "match_id": match_id, "new_dispatch_status": new_status}


@router.get("/bipartite_graph")
async def get_bipartite_graph_data():
    """
    Returns graph topology (demands as targets, hubs as sources, allocations as weighted edges)
    for UI geospatial and bipartite node visualizers.
    """
    plan = crisis_db.latest_plan or crisis_db.run_matching_cycle()

    demand_nodes = []
    for req_id, dem in crisis_db.raw_demands.items():
        triage = crisis_db.triage_records.get(req_id)
        demand_nodes.append({
            "id": dem.request_id,
            "type": "DEMAND",
            "name": dem.requester_name,
            "lat": dem.latitude,
            "lon": dem.longitude,
            "urgency": dem.urgency_score,
            "category": triage.primary_category.value if triage else "GENERAL",
            "headcount": dem.headcount,
            "zone_id": dem.zone_id
        })

    hub_nodes = []
    for hub_id, hub in crisis_db.supply_hubs.items():
        hub_nodes.append({
            "id": hub.hub_id,
            "type": "HUB",
            "name": hub.name,
            "lat": hub.latitude,
            "lon": hub.longitude,
            "status": hub.operational_status,
            "available_vehicles": hub.available_vehicles,
            "stock_count": sum(i.quantity for i in hub.inventory.values())
        })

    edges = []
    for m in plan.matches:
        edges.append({
            "match_id": m.match_id,
            "source_hub_id": m.hub_id,
            "target_request_id": m.request_id,
            "distance_km": m.distance_km,
            "transit_minutes": m.estimated_transit_minutes,
            "score": m.urgency_weighted_score,
            "status": m.dispatch_status,
            "items": m.items_allocated
        })

    return {
        "plan_id": plan.plan_id,
        "gini_index": plan.gini_equity_index,
        "fulfillment_rate": plan.fulfillment_rate_percent,
        "nodes": {
            "demands": demand_nodes,
            "hubs": hub_nodes
        },
        "edges": edges
    }
