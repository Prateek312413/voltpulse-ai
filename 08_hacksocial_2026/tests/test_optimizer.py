"""
Unit Tests for Bipartite Resource Matching & Equity Optimizer
"""

import pytest
from core.resource_optimizer import ResourceOptimizer, SupplyHub, SupplyItem, DemandRequest


@pytest.fixture
def optimizer():
    return ResourceOptimizer(fairness_weight=0.35, distance_penalty_weight=0.05)


def test_haversine_distance(optimizer):
    # San Francisco (37.7749, -122.4194) to Oakland (37.8044, -122.2712) ~ 13.5 km
    dist = optimizer.haversine_distance(37.7749, -122.4194, 37.8044, -122.2712)
    assert 12.0 <= dist <= 15.0


def test_gini_coefficient_calculation(optimizer):
    # Perfect equality
    equal_zones = {"Z1": (10.0, 10.0), "Z2": (10.0, 10.0), "Z3": (10.0, 10.0)}
    assert optimizer.calculate_gini_index(equal_zones) == 0.0

    # Extreme inequality
    unequal_zones = {"Z1": (10.0, 10.0), "Z2": (0.0, 50.0), "Z3": (0.0, 100.0)}
    gini = optimizer.calculate_gini_index(unequal_zones)
    assert gini > 0.40


def test_bipartite_matching_execution(optimizer):
    hubs = [
        SupplyHub(
            hub_id="H1",
            name="Main Warehouse",
            latitude=37.77,
            longitude=-122.41,
            inventory={
                "potable_water": SupplyItem(item_id="W1", name="Water", category="WATER", quantity=100, unit="gal"),
                "insulin": SupplyItem(item_id="I1", name="Insulin", category="MED", quantity=10, unit="vials", is_perishable=True)
            }
        ),
        SupplyHub(
            hub_id="H2_OFFLINE",
            name="Blocked Hub",
            latitude=37.78,
            longitude=-122.42,
            operational_status="OFFLINE",
            inventory={
                "potable_water": SupplyItem(item_id="W1", name="Water", category="WATER", quantity=500, unit="gal")
            }
        )
    ]

    demands = [
        DemandRequest(
            request_id="D1",
            requester_name="Diabetic Patient",
            latitude=37.772,
            longitude=-122.412,
            urgency_score=9.5,
            headcount=1,
            required_items={"insulin": 2, "potable_water": 5},
            zone_id="ZONE-A"
        ),
        DemandRequest(
            request_id="D2",
            requester_name="Community Shelter",
            latitude=37.775,
            longitude=-122.415,
            urgency_score=7.0,
            headcount=10,
            required_items={"potable_water": 40},
            zone_id="ZONE-B"
        )
    ]

    plan = optimizer.optimize_allocations(demands, hubs)

    assert plan.total_demands == 2
    assert plan.matched_demands == 2
    assert plan.unfulfilled_demands == 0
    assert plan.fulfillment_rate_percent == 100.0
    # Make sure offline hub was never used
    for m in plan.matches:
        assert m.hub_id == "H1"
