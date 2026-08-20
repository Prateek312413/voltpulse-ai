"""
Unit Tests for ProcurePulse MCDA Ranking Engine.
"""

from backend.ranking_engine import RankingEngine
from skills.procure_pulse_negotiator.schemas import (
    SupplierBidResult,
    QuoteExtraction,
    VolumeTier,
    CallDisposition,
    StockStatus,
)


def test_mcda_bid_ranking():
    # Supplier 1: Lower price, 2 days lead time
    q1 = QuoteExtraction(
        rfq_id="RFQ-TEST-01",
        supplier_name="Apex Industrial Fasteners",
        call_disposition=CallDisposition.QUOTE_RECEIVED,
        sku_quoted="SS-400-1-4",
        base_unit_price=42.50,
        lead_time_days=2,
        volume_tiers=[
            VolumeTier(min_quantity=250, unit_price=42.50),
            VolumeTier(min_quantity=500, unit_price=38.00),
        ],
    )
    b1 = SupplierBidResult(
        supplier_id="sup-apex",
        supplier_name="Apex Industrial Fasteners",
        phone_number="+18005550199",
        supplier_rating=4.8,
        quote=q1,
    )

    # Supplier 2: Higher price ($44.00), 1 day lead time, high rating (4.9)
    q2 = QuoteExtraction(
        rfq_id="RFQ-TEST-01",
        supplier_name="Midwest Fluid Controls",
        call_disposition=CallDisposition.QUOTE_RECEIVED,
        sku_quoted="SS-400-1-4",
        base_unit_price=44.00,
        lead_time_days=1,
        volume_tiers=[VolumeTier(min_quantity=250, unit_price=44.00)],
    )
    b2 = SupplierBidResult(
        supplier_id="sup-midwest",
        supplier_name="Midwest Fluid Controls",
        phone_number="+18005550188",
        supplier_rating=4.9,
        quote=q2,
    )

    # Supplier 3: Low price ($41.00) but 5 days lead time and $65 freight
    q3 = QuoteExtraction(
        rfq_id="RFQ-TEST-01",
        supplier_name="Titan Bearing",
        call_disposition=CallDisposition.QUOTE_RECEIVED,
        sku_quoted="SS-400-1-4",
        base_unit_price=41.00,
        lead_time_days=5,
        estimated_freight_cost=65.0,
        freight_terms="FOB Origin",
    )
    b3 = SupplierBidResult(
        supplier_id="sup-titan",
        supplier_name="Titan Bearing",
        phone_number="+18005550177",
        supplier_rating=4.6,
        quote=q3,
    )

    ranked = RankingEngine.rank_bids([b1, b2, b3], target_qty=250, target_unit_budget=45.00)

    assert len(ranked) == 3
    assert ranked[0].is_recommended is True
    assert ranked[0].rank == 1
    assert ranked[0].mcda_score > ranked[1].mcda_score
    assert ranked[0].potential_savings > 0.0
