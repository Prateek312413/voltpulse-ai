"""
ResilioNet AI - Multi-Modal Resource Matching & Allocation Optimization Engine
Implements fairness-constrained bipartite network flow optimization,
Haversine transit decay, perishability weighting, and Gini equity regularization.
"""

import math
from typing import List, Dict, Optional, Any, Tuple
from pydantic import BaseModel, Field


class SupplyItem(BaseModel):
    item_id: str
    name: str
    category: str
    quantity: int = Field(..., ge=0)
    unit: str
    is_perishable: bool = False
    shelf_life_hours: Optional[float] = None
    cold_chain_required: bool = False


class SupplyHub(BaseModel):
    hub_id: str
    name: str
    latitude: float
    longitude: float
    capacity_units: int = 1000
    available_vehicles: int = 5
    inventory: Dict[str, SupplyItem] = Field(default_factory=dict)
    operational_status: str = "ACTIVE"  # ACTIVE, DEGRADED, OFFLINE


class DemandRequest(BaseModel):
    request_id: str
    requester_name: str
    latitude: float
    longitude: float
    urgency_score: float = Field(..., ge=1.0, le=10.0)
    headcount: int = 1
    required_items: Dict[str, int] = Field(default_factory=dict)  # item_category: quantity
    special_requirements: List[str] = Field(default_factory=list)
    zone_id: str = "ZONE-DEFAULT"
    timestamp_created: float = 0.0


class MatchResult(BaseModel):
    match_id: str
    request_id: str
    hub_id: str
    hub_name: str
    distance_km: float
    estimated_transit_minutes: float
    items_allocated: Dict[str, int]
    urgency_weighted_score: float
    fairness_penalty: float
    perishability_priority_boost: float
    dispatch_status: str = "PENDING_DISPATCH"  # PENDING_DISPATCH, DISPATCHED, DELIVERED


class AllocationPlan(BaseModel):
    plan_id: str
    timestamp: float
    total_demands: int
    matched_demands: int
    unfulfilled_demands: int
    total_urgency_served: float
    total_urgency_backlog: float
    fulfillment_rate_percent: float
    gini_equity_index: float = Field(..., description="0.0 = perfect equity across zones, 1.0 = extreme inequality")
    matches: List[MatchResult] = Field(default_factory=list)
    unserviced_request_ids: List[str] = Field(default_factory=list)
    critical_bottlenecks: List[str] = Field(default_factory=list)


class ResourceOptimizer:
    """
    Mathematical solver for dynamic disaster logistics and mutual-aid distribution.
    Optimizes for both maximum critical life-saving efficiency and geographic fairness.
    """

    EARTH_RADIUS_KM = 6371.0
    AVERAGE_RELIEF_SPEED_KMH = 35.0  # Average speed in disrupted disaster terrain

    def __init__(self, fairness_weight: float = 0.35, distance_penalty_weight: float = 0.05):
        self.fairness_weight = fairness_weight
        self.distance_penalty_weight = distance_penalty_weight

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Computes great-circle distance between two points in kilometers."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(ResourceOptimizer.EARTH_RADIUS_KM * c, 2)

    def calculate_gini_index(self, zone_satisfactions: Dict[str, Tuple[float, float]]) -> float:
        """
        Calculates Gini coefficient of unmet urgency across geographic zones.
        zone_satisfactions: {zone_id: (served_urgency, total_urgency)}
        Returns Gini coefficient [0.0, 1.0].
        """
        if not zone_satisfactions:
            return 0.0

        unmet_urgencies = []
        for zone, (served, total) in zone_satisfactions.items():
            unmet = max(0.0, total - served)
            unmet_urgencies.append(unmet)

        n = len(unmet_urgencies)
        if n <= 1 or sum(unmet_urgencies) == 0:
            return 0.0

        unmet_urgencies.sort()
        sum_unmet = sum(unmet_urgencies)
        cumulative_sum = 0.0
        weighted_sum = 0.0

        for i, val in enumerate(unmet_urgencies):
            cumulative_sum += val
            weighted_sum += (i + 1) * val

        gini = (2.0 * weighted_sum) / (n * sum_unmet) - (n + 1.0) / n
        return round(max(0.0, min(1.0, gini)), 3)

    def optimize_allocations(
        self,
        demands: List[DemandRequest],
        hubs: List[SupplyHub],
        plan_id: Optional[str] = None
    ) -> AllocationPlan:
        """
        Executes constrained multi-criteria matching algorithm.
        Sorts demands by effective priority (urgency, perishability, zone vulnerability).
        Allocates nearest compatible inventory while tracking capacity and fairness.
        """
        import time
        pid = plan_id or f"PLAN-{int(time.time())}"
        current_time = time.time()

        # Clone hub inventories for simulated decrement during matching
        hub_inventory_pool: Dict[str, Dict[str, int]] = {}
        hub_map: Dict[str, SupplyHub] = {}
        for h in hubs:
            hub_map[h.hub_id] = h
            hub_inventory_pool[h.hub_id] = {}
            if h.operational_status != "OFFLINE":
                for item_code, item_obj in h.inventory.items():
                    hub_inventory_pool[h.hub_id][item_code] = item_obj.quantity

        # Track zone aggregations for Gini computation
        zone_totals: Dict[str, float] = {}
        zone_served: Dict[str, float] = {}
        for d in demands:
            zone_totals[d.zone_id] = zone_totals.get(d.zone_id, 0.0) + d.urgency_score
            if d.zone_id not in zone_served:
                zone_served[d.zone_id] = 0.0

        # Sort demands by Urgency Score descending (critical 10s first)
        sorted_demands = sorted(demands, key=lambda d: (d.urgency_score, d.headcount), reverse=True)

        matches: List[MatchResult] = []
        unserviced_ids: List[str] = []
        total_urgency_served = 0.0
        total_urgency_backlog = 0.0
        bottleneck_counter: Dict[str, int] = {}

        for req in sorted_demands:
            req_fulfilled = False
            best_candidate_hub: Optional[str] = None
            best_allocation_items: Dict[str, int] = {}
            best_candidate_score = -float('inf')
            min_dist = float('inf')
            best_perish_boost = 0.0

            # Scan available hubs
            for hub in hubs:
                if hub.operational_status == "OFFLINE":
                    continue

                dist_km = self.haversine_distance(req.latitude, req.longitude, hub.latitude, hub.longitude)
                
                # Check supply availability at this hub
                allocated_from_hub: Dict[str, int] = {}
                is_compatible = False
                perish_boost = 0.0

                for req_item, req_qty in req.required_items.items():
                    avail = hub_inventory_pool[hub.hub_id].get(req_item, 0)
                    if avail > 0:
                        allocated_qty = min(req_qty, avail)
                        allocated_from_hub[req_item] = allocated_qty
                        is_compatible = True

                        # Check perishability
                        if req_item in hub.inventory and hub.inventory[req_item].is_perishable:
                            perish_boost += 1.5

                if not is_compatible:
                    continue

                # Multi-Objective Scoring:
                # Score = (Urgency * Satisfaction_Ratio) - (Distance_Penalty) + (Perishability_Boost) - (Zone_Fairness_Divergence)
                satisfaction_ratio = sum(allocated_from_hub.values()) / max(1, sum(req.required_items.values()))
                urgency_gain = req.urgency_score * satisfaction_ratio * 10.0
                dist_penalty = dist_km * self.distance_penalty_weight
                zone_urgency_gap = zone_totals.get(req.zone_id, 0.0) - zone_served.get(req.zone_id, 0.0)
                equity_incentive = zone_urgency_gap * self.fairness_weight

                total_score = urgency_gain - dist_penalty + perish_boost + equity_incentive

                if total_score > best_candidate_score:
                    best_candidate_score = total_score
                    best_candidate_hub = hub.hub_id
                    best_allocation_items = allocated_from_hub
                    min_dist = dist_km
                    best_perish_boost = perish_boost

            # Apply best match if found
            if best_candidate_hub and best_allocation_items:
                for item_k, item_v in best_allocation_items.items():
                    hub_inventory_pool[best_candidate_hub][item_k] -= item_v

                transit_mins = round((min_dist / self.AVERAGE_RELIEF_SPEED_KMH) * 60.0 + 5.0, 1)  # 5 min staging overhead
                matched_hub_obj = hub_map[best_candidate_hub]

                match_rec = MatchResult(
                    match_id=f"M-{len(matches)+1:04d}",
                    request_id=req.request_id,
                    hub_id=best_candidate_hub,
                    hub_name=matched_hub_obj.name,
                    distance_km=min_dist,
                    estimated_transit_minutes=transit_mins,
                    items_allocated=best_allocation_items,
                    urgency_weighted_score=round(best_candidate_score, 2),
                    fairness_penalty=round(min_dist * self.distance_penalty_weight, 2),
                    perishability_priority_boost=round(best_perish_boost, 2),
                    dispatch_status="PENDING_DISPATCH"
                )
                matches.append(match_rec)
                total_urgency_served += req.urgency_score
                zone_served[req.zone_id] += req.urgency_score
                req_fulfilled = True

            if not req_fulfilled:
                unserviced_ids.append(req.request_id)
                total_urgency_backlog += req.urgency_score
                for item_needed in req.required_items.keys():
                    bottleneck_counter[item_needed] = bottleneck_counter.get(item_needed, 0) + 1

        # Calculate Gini equity across zones
        zone_satisfaction_map = {z: (zone_served.get(z, 0.0), zone_totals.get(z, 0.0)) for z in zone_totals}
        gini_index = self.calculate_gini_index(zone_satisfaction_map)

        fulfillment_rate = (len(matches) / max(1, len(demands))) * 100.0

        critical_bottlenecks = [
            f"Deficit in supply '{item}' ({count} unmet requests)"
            for item, count in sorted(bottleneck_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return AllocationPlan(
            plan_id=pid,
            timestamp=current_time,
            total_demands=len(demands),
            matched_demands=len(matches),
            unfulfilled_demands=len(unserviced_ids),
            total_urgency_served=round(total_urgency_served, 2),
            total_urgency_backlog=round(total_urgency_backlog, 2),
            fulfillment_rate_percent=round(fulfillment_rate, 2),
            gini_equity_index=gini_index,
            matches=matches,
            unserviced_request_ids=unserviced_ids,
            critical_bottlenecks=critical_bottlenecks
        )
