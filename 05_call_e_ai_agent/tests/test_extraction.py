"""
Unit Tests for ProcurePulse Extraction Engine.
"""

from backend.extraction_engine import ExtractionEngine
from skills.procure_pulse_negotiator.schemas import CallDisposition, StockStatus


def test_spoken_price_and_tier_extraction():
    transcript = (
        "[CalleAgent] Hello, calling regarding quote for SS-400-1-4 x 250 units.\n"
        "[Supplier] Hi, this is Sarah. For 250 units, our price is forty-two fifty each.\n"
        "[CalleAgent] Do you offer volume discounts for 500 or 1,000 units?\n"
        "[Supplier] If you bump that up to five hundred, that drops to thirty-eight even. At a thousand, it drops to thirty-four twenty.\n"
        "[CalleAgent] When can that ship?\n"
        "[Supplier] In stock, standard ground transit is 2 business days. Freight is prepaid FOB Destination.\n"
        "[CalleAgent] Thank you. Quote reference Q-88192-A logged.\n"
    )

    extraction = ExtractionEngine.extract_from_transcript(
        rfq_id="RFQ-TEST-01",
        supplier_name="Apex Industrial Fasteners",
        transcript_text=transcript,
        target_sku="SS-400-1-4",
        target_qty=250,
        target_budget=45.00,
    )

    assert extraction.base_unit_price == 42.50
    assert extraction.lead_time_days == 2
    assert extraction.stock_status == StockStatus.IN_STOCK
    assert len(extraction.volume_tiers) == 3
    assert extraction.volume_tiers[1].unit_price == 38.00
    assert extraction.volume_tiers[2].unit_price == 34.20
    assert len(extraction.grounded_citations) >= 2


def test_substitute_sku_detection():
    transcript = (
        "[CalleAgent] Requesting quote for SS-400-1-4.\n"
        "[Supplier] The OEM SKU is backordered, but we have our direct replacement SS-400-1-4-EQUIV in stock for $39.50 each.\n"
        "[Supplier] Ships same-day for 1-day delivery.\n"
    )

    extraction = ExtractionEngine.extract_from_transcript(
        rfq_id="RFQ-TEST-02",
        supplier_name="Precision Metals",
        transcript_text=transcript,
        target_sku="SS-400-1-4",
        target_qty=250,
        target_budget=45.00,
    )

    assert extraction.is_exact_match is False
    assert extraction.sku_quoted == "SS-400-1-4-EQUIV"
    assert extraction.substitute_offered is not None
    assert extraction.base_unit_price == 39.50
