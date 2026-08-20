#!/usr/bin/env python3
"""
Dry-run test script for ProcurePulse Negotiator skill.
Validates inputs, prompt generation, schema validation, and test simulations.
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add skill path to sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from schemas import (
    ProcurementCallGoal,
    RequestedPart,
    QuoteExtraction,
    VolumeTier,
    GroundedCitation,
    CallDisposition,
    StockStatus,
)


def run_dry_run_test():
    print("=" * 60)
    print("[TEST] Running ProcurePulse Negotiator Skill Dry-Run Verification")
    print("=" * 60)

    # 1. Create sample procurement call request
    sample_part = RequestedPart(
        sku="SS-400-1-4",
        description="1/4 in. 316 Stainless Steel High Pressure Ball Valve, 1000 PSI",
        target_quantity=250,
        target_unit_budget=45.00,
        required_delivery_date="2026-09-01",
    )

    goal = ProcurementCallGoal(
        rfq_id="RFQ-2026-0891",
        supplier_name="Apex Industrial Fasteners",
        to_phone_e164="+18005550199",
        company_name="VoltPulse Manufacturing Corp",
        buyer_contact_name="Alex Morgan",
        buyer_contact_email="alex.morgan@voltpulse.ai",
        parts_requested=[sample_part],
        volume_tier_checks=[250, 500, 1000],
        preferred_freight_terms="FOB Destination, Ground",
    )

    print("\n[Step 1] Input Validation: PASSED")
    print(f"  RFQ ID: {goal.rfq_id}")
    print(f"  Supplier: {goal.supplier_name} ({goal.to_phone_e164})")
    print(f"  Part: {sample_part.sku} x {sample_part.target_quantity} units (Budget: ${sample_part.target_unit_budget}/unit)")

    # 2. Synthesize CALL-E prompt
    prompt = goal.to_calle_prompt()
    print("\n[Step 2] Synthesized CALL-E Prompt Preview:")
    print("-" * 40)
    print(prompt[:350] + "...\n[Full prompt: " + str(len(prompt)) + " characters]")
    print("-" * 40)
    assert "Apex Industrial Fasteners" in prompt
    assert "SS-400-1-4" in prompt
    assert "DO NOT commit to purchasing" in prompt
    print("  Prompt checks: PASSED")

    # 3. Simulate Structured Extraction
    mock_quote = QuoteExtraction(
        rfq_id=goal.rfq_id,
        supplier_name=goal.supplier_name,
        call_disposition=CallDisposition.QUOTE_RECEIVED,
        representative_name="Sarah Miller",
        quote_reference_number="Q-88192-A",
        sku_quoted="SS-400-1-4",
        is_exact_match=True,
        stock_status=StockStatus.IN_STOCK,
        lead_time_days=2,
        base_unit_price=42.50,
        volume_tiers=[
            VolumeTier(min_quantity=250, unit_price=42.50, savings_percent=5.56),
            VolumeTier(min_quantity=500, unit_price=38.00, savings_percent=15.56),
            VolumeTier(min_quantity=1000, unit_price=34.20, savings_percent=24.00),
        ],
        freight_terms="FOB Destination, Ground included over $500",
        estimated_freight_cost=0.0,
        grounded_citations=[
            GroundedCitation(
                claim="Unit price at 250 units is $42.50",
                verbatim_quote="For 250 of the SS-400s, I can do forty-two fifty each.",
                timestamp_seconds=38,
            ),
            GroundedCitation(
                claim="Tier discount at 500 units is $38.00",
                verbatim_quote="If you bump that up to five hundred, that drops to thirty-eight even.",
                timestamp_seconds=54,
            ),
            GroundedCitation(
                claim="In stock with 2-day ground shipping",
                verbatim_quote="We have six hundred on the shelf right now in our Dallas warehouse, can ship today for two-day arrival.",
                timestamp_seconds=68,
            ),
        ],
        notes="Spoke with Sarah in commercial sales. Mill test reports included at no charge.",
    )

    print("\n[Step 3] Output Schema Serialization Test:")
    quote_json = mock_quote.model_dump_json(indent=2)
    print(quote_json[:400] + "\n  ...")
    assert mock_quote.base_unit_price == 42.50
    assert len(mock_quote.volume_tiers) == 3
    assert len(mock_quote.grounded_citations) == 3
    print("  Schema Validation: PASSED")

    print("\n" + "=" * 60)
    print("[SUCCESS] All ProcurePulse Skill Dry-Run tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_dry_run_test()
