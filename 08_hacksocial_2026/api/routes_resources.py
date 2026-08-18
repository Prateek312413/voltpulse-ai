"""
ResilioNet AI - Supply Depots & Mutual-Aid Inventory Endpoints
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
try:
    from core.state import crisis_db
    from core.resource_optimizer import SupplyHub, SupplyItem
except ImportError:
    from ..core.state import crisis_db
    from ..core.resource_optimizer import SupplyHub, SupplyItem

router = APIRouter()


class InventoryUpdateRequest(BaseModel):
    item_id: str
    name: str
    category: str
    quantity_delta: int = Field(..., description="Positive to add stock, negative to consume/dispatch")
    unit: str = "units"
    is_perishable: bool = False


class HubStatusUpdateRequest(BaseModel):
    operational_status: str = Field(..., description="ACTIVE, DEGRADED, OFFLINE")


class DepotRegistrationRequest(BaseModel):
    hub_id: str
    name: str
    latitude: float
    longitude: float
    capacity_units: int = 1000
    available_vehicles: int = 5


@router.get("/hubs", response_model=List[SupplyHub])
async def list_supply_hubs():
    """Lists all registered emergency warehouses, mutual aid food banks, and supply depots."""
    return list(crisis_db.supply_hubs.values())


@router.get("/hubs/{hub_id}", response_model=SupplyHub)
async def get_supply_hub(hub_id: str):
    """Fetches details and real-time inventory of a specific depot."""
    if hub_id not in crisis_db.supply_hubs:
        raise HTTPException(status_code=404, detail=f"Hub ID '{hub_id}' not found")
    return crisis_db.supply_hubs[hub_id]


@router.post("/hubs/register", response_model=SupplyHub)
async def register_supply_hub(req: DepotRegistrationRequest):
    """Registers a new community mutual aid hub or NGO warehouse on the resilience grid."""
    if req.hub_id in crisis_db.supply_hubs:
        raise HTTPException(status_code=400, detail=f"Hub ID '{req.hub_id}' already registered")

    hub = SupplyHub(
        hub_id=req.hub_id,
        name=req.name,
        latitude=req.latitude,
        longitude=req.longitude,
        capacity_units=req.capacity_units,
        available_vehicles=req.available_vehicles,
        inventory={},
        operational_status="ACTIVE"
    )
    crisis_db.supply_hubs[hub.hub_id] = hub

    crisis_db.audit_ledger.append_event("DEPOT_REGISTERED", {
        "hub_id": hub.hub_id,
        "name": hub.name,
        "location": [hub.latitude, hub.longitude]
    })
    return hub


@router.post("/hubs/{hub_id}/inventory/update", response_model=SupplyHub)
async def update_hub_inventory(hub_id: str, req: InventoryUpdateRequest):
    """Updates supply counts (restock or field dispatch) and audits the transaction."""
    if hub_id not in crisis_db.supply_hubs:
        raise HTTPException(status_code=404, detail=f"Hub ID '{hub_id}' not found")

    hub = crisis_db.supply_hubs[hub_id]
    item_code = req.name.lower().replace(" ", "_")

    if item_code in hub.inventory:
        current_qty = hub.inventory[item_code].quantity
        new_qty = max(0, current_qty + req.quantity_delta)
        hub.inventory[item_code].quantity = new_qty
    else:
        new_qty = max(0, req.quantity_delta)
        hub.inventory[item_code] = SupplyItem(
            item_id=req.item_id,
            name=req.name,
            category=req.category,
            quantity=new_qty,
            unit=req.unit,
            is_perishable=req.is_perishable
        )

    crisis_db.audit_ledger.append_event("INVENTORY_UPDATED", {
        "hub_id": hub_id,
        "item": req.name,
        "delta": req.quantity_delta,
        "new_quantity": new_qty
    })

    # Trigger re-optimization
    crisis_db.run_matching_cycle()
    return hub


@router.post("/hubs/{hub_id}/status", response_model=SupplyHub)
async def update_hub_status(hub_id: str, req: HubStatusUpdateRequest):
    """Sets depot operational status (ACTIVE, DEGRADED, OFFLINE) to simulate disrupted nodes."""
    if hub_id not in crisis_db.supply_hubs:
        raise HTTPException(status_code=404, detail=f"Hub ID '{hub_id}' not found")

    status = req.operational_status.upper()
    if status not in ["ACTIVE", "DEGRADED", "OFFLINE"]:
        raise HTTPException(status_code=400, detail="Status must be ACTIVE, DEGRADED, or OFFLINE")

    hub = crisis_db.supply_hubs[hub_id]
    hub.operational_status = status

    crisis_db.audit_ledger.append_event("DEPOT_STATUS_ALTERED", {
        "hub_id": hub_id,
        "new_status": status
    })

    crisis_db.run_matching_cycle()
    return hub
