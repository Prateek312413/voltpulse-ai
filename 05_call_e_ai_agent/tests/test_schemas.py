"""
Unit Tests for ProcurePulse Schemas and Prompt Construction.
"""

import pytest
from skills.procure_pulse_negotiator.schemas import (
    ProcurementCallGoal,
    RequestedPart,
    QuoteExtraction,
    VolumeTier,
    CallDisposition,
    StockStatus,
)


def test_valid_procurement_goal_prompt():
    part = RequestedPart(
        sku="SS-400-1-4",
        description="1/4 in. 316 Stainless Steel Ball Valve",
        target_quantity=250,
        target_unit_budget=45.0,
    )
    goal = ProcurementCallGoal(
        rfq_id="RFQ-TEST-01",
        supplier_name="Apex Industrial Fasteners",
        to_phone_e164="+18005550199",
        parts_requested=[part],
    )
    prompt = goal.to_calle_prompt()

    assert "Apex Industrial Fasteners" in prompt
    assert "SS-400-1-4" in prompt
    assert "250" in prompt
    assert "$45.00" in prompt
    assert "DO NOT commit to purchasing" in prompt


def test_invalid_phone_number():
    part = RequestedPart(
        sku="SS-400-1-4",
        description="Valve",
        target_quantity=100,
        target_unit_budget=50.0,
    )
    with pytest.raises(ValueError, match="not a valid E.164 format"):
        ProcurementCallGoal(
            rfq_id="RFQ-TEST-02",
            supplier_name="Test Supplier",
            to_phone_e164="18005550199",  # Missing leading +
            parts_requested=[part],
        )


def test_volume_tier_savings_calculation():
    tier = VolumeTier(min_quantity=500, unit_price=38.00, savings_percent=15.56)
    assert tier.min_quantity == 500
    assert tier.unit_price == 38.00
    assert tier.savings_percent == 15.56
