"""
ProcurePulse CALL-E High-Fidelity Voice Simulator
Generates realistic multi-turn supplier negotiation dialogues, audio waveforms,
and grounded structured quotes for seamless zero-credit demoing & test verification.
"""

import asyncio
import random
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from skills.procure_pulse_negotiator.schemas import (
    QuoteExtraction,
    VolumeTier,
    GroundedCitation,
    SubstitutePart,
    CallDisposition,
    StockStatus,
)


SUPPLIER_PERSONAS = {
    "sup-apex": {
        "name": "Apex Industrial Fasteners & Valves",
        "rep": "Sarah Miller",
        "quote_ref": "Q-88192-A",
        "base_price_factor": 0.944,  # $42.50 against $45.00
        "tiers": [(250, 42.50), (500, 38.00), (1000, 34.20)],
        "lead_time_days": 2,
        "stock_status": StockStatus.IN_STOCK,
        "freight_terms": "FOB Destination (Free Ground over $500)",
        "freight_cost": 0.0,
        "substitute": None,
        "notes": "Large stock in Dallas warehouse. Mill test certs included.",
        "script_template": [
            (0, "System", "Dialing +18005550199... Ringing... Connected."),
            (3, "CalleAgent", "Hello! This is an automated inquiry on behalf of VoltPulse Manufacturing's procurement team regarding a commercial price and availability quote for part number {sku}."),
            (8, "Supplier", "Hi there, yes, this is Sarah with commercial sales at Apex. Let me pull up that part number in our catalog... Okay, I see {sku}, the {description}."),
            (16, "CalleAgent", "Great. Could you verify if that SKU is currently in stock for immediate dispatch, and what your unit price is for an order of {qty} units?"),
            (24, "Supplier", "We have about six hundred units sitting on the shelf right now in our Dallas facility. For {qty} units, our standard commercial price is forty-two dollars and fifty cents each."),
            (32, "CalleAgent", "Understood, $42.50 per unit. Do you offer tiered volume pricing if we were to increase the batch size to 500 or 1,000 units?"),
            (40, "Supplier", "Yes, absolutely. If you bump that up to five hundred units, we can drop the price to thirty-eight dollars even. And if you go up to a thousand units, it drops to thirty-four twenty."),
            (49, "CalleAgent", "That is very helpful. What is the estimated lead time, and how is freight handled?"),
            (56, "Supplier", "We can pack and ship today. Standard ground transit to your plant is two business days. And on orders over five hundred dollars, ground freight is completely prepaid and covered by us."),
            (65, "CalleAgent", "Perfect. Thank you Sarah. I am recording these details for our procurement manager Alex Morgan to review and issue the formal Purchase Order. Could I confirm your quote reference number?"),
            (73, "Supplier", "Sure thing! Reference number is Q-88192-A. Ask for Sarah if you have any questions."),
            (79, "CalleAgent", "Thank you Sarah. Have a wonderful day! Goodbye."),
            (83, "System", "Call ended normally. Total duration: 83s. Processing transcript and extracting structured quote..."),
        ],
    },
    "sup-midwest": {
        "name": "Midwest Fluid Controls",
        "rep": "David Vance",
        "quote_ref": "MFC-2026-904",
        "base_price_factor": 0.978,  # $44.00 against $45.00
        "tiers": [(250, 44.00), (500, 41.20), (1000, 37.50)],
        "lead_time_days": 1,
        "stock_status": StockStatus.IN_STOCK,
        "freight_terms": "FOB Destination (Next-Day Priority Ground)",
        "freight_cost": 0.0,
        "substitute": None,
        "notes": "Highest reliability rating (4.9/5). 1-day turnaround with certified MTR documentation.",
        "script_template": [
            (0, "System", "Dialing +18005550188... Ringing... Connected."),
            (3, "CalleAgent", "Hello! This is an automated inquiry on behalf of VoltPulse Manufacturing regarding part number {sku}."),
            (8, "Supplier", "Midwest Fluid Controls, David speaking. How can I help you today?"),
            (14, "CalleAgent", "Hello David. We are requesting a commercial quote and lead time verification for {qty} units of part {sku}."),
            (22, "Supplier", "Let me check the central warehouse. Yes, we have over 1,200 of the {sku} in stock in Chicago. For {qty} units, we can quote $44.00 per unit."),
            (30, "CalleAgent", "Thank you David. Do you provide volume discount tiers for 500 or 1,000 units?"),
            (37, "Supplier", "At 500 units, we can do $41.20. At 1,000 units, we can offer $37.50 per unit with free priority freight."),
            (46, "CalleAgent", "What is the dispatch timeline and transit time?"),
            (52, "Supplier", "Since you're in the central region, orders placed before 3 PM ship same-day for guaranteed next-day delivery."),
            (60, "CalleAgent", "Understood. I will log this quote under reference MFC-2026-904 for our purchasing lead Alex Morgan to review."),
            (68, "Supplier", "Sounds great. We look forward to fulfilling the order."),
            (73, "System", "Call ended normally. Total duration: 73s."),
        ],
    },
    "sup-titan": {
        "name": "Titan Bearing & Hardware Co.",
        "rep": "Mark Reynolds",
        "quote_ref": "TB-5541-Q",
        "base_price_factor": 0.911,  # $41.00 against $45.00
        "tiers": [(250, 41.00), (500, 39.00), (1000, 36.00)],
        "lead_time_days": 5,
        "stock_status": StockStatus.IN_STOCK,
        "freight_terms": "FOB Origin ($65 Freight billed separately)",
        "freight_cost": 65.0,
        "substitute": None,
        "notes": "Low base price but longer 5-day factory transit and separate freight billing.",
        "script_template": [
            (0, "System", "Dialing +18005550177... Ringing... Connected."),
            (3, "CalleAgent", "Hello, calling Titan Bearing on behalf of VoltPulse Manufacturing regarding RFQ for {sku}."),
            (9, "Supplier", "Titan Parts, Mark speaking. Looking for {sku}?"),
            (15, "CalleAgent", "Yes, checking availability and unit pricing for {qty} units of {sku}."),
            (23, "Supplier", "We have allocation at our Cleveland hub. Unit price is $41.00 at {qty} pieces. Tier at 500 is $39.00, tier at 1,000 is $36.00."),
            (32, "CalleAgent", "What is the lead time and shipping term?"),
            (39, "Supplier", "Lead time is approximately 5 business days. Freight is FOB origin, estimate around sixty-five dollars freight for the crate."),
            (48, "CalleAgent", "Understood. Logging quote reference TB-5541-Q for purchasing approval. Thank you Mark!"),
            (55, "System", "Call ended normally. Total duration: 55s."),
        ],
    },
    "sup-precision": {
        "name": "Precision Metals & Component Direct",
        "rep": "Karen Lewis",
        "quote_ref": "PMC-7720-X",
        "base_price_factor": 0.877,  # $39.50 substitute
        "tiers": [(250, 39.50), (500, 36.00), (1000, 32.50)],
        "lead_time_days": 1,
        "stock_status": StockStatus.IN_STOCK,
        "freight_terms": "FOB Destination (Free Express Freight)",
        "freight_cost": 0.0,
        "substitute": SubstitutePart(
            substitute_sku="SS-400-1-4-EQUIV",
            manufacturer="Precision Flow Systems",
            description="316SS Ball Valve 1000 PSI, Exact Spec Match, Lifetime Seal Warranty",
            unit_price=39.50,
            spec_compatibility="100% Form-Fit-Function Equivalent with Upgraded PTFE Seats",
        ),
        "notes": "Original OEM SKU backordered 3 weeks, but offered certified direct equivalent at $39.50 with immediate dispatch!",
        "script_template": [
            (0, "System", "Dialing +18005550166... Ringing... Connected."),
            (3, "CalleAgent", "Hello! Calling Precision Metals on behalf of VoltPulse Manufacturing regarding quote for part number {sku}."),
            (9, "Supplier", "Hello, Karen with key accounts here. Checking {sku}..."),
            (16, "Supplier", "The OEM branded {sku} is currently backordered for 3 weeks across the distributor network. However, we have 800 units of our direct certified drop-in replacement, part SS-400-1-4-EQUIV in stock right now."),
            (27, "CalleAgent", "What are the specifications and price on the SS-400-1-4-EQUIV equivalent for {qty} units?"),
            (35, "Supplier", "It is 100% form-fit-function compatible, same 316 stainless steel, tested to 1000 PSI, and we can offer it at $39.50 per unit. At 500 units it is $36.00, and at 1,000 units it is $32.50."),
            (46, "CalleAgent", "When can that ship, and what are the freight terms?"),
            (52, "Supplier", "It can ship today for 1-day delivery with free express freight included."),
            (60, "CalleAgent", "Excellent. I will note the substitute specification and quote PMC-7720-X for our engineering and purchasing team to review. Thank you Karen!"),
            (68, "System", "Call ended normally. Total duration: 68s."),
        ],
    },
}


class CalleSimulator:
    """High-fidelity voice call simulator for zero-credit testing and automated demos."""

    @staticmethod
    async def simulate_call_stream(
        supplier_id: str,
        sku: str,
        description: str,
        target_qty: int,
        target_budget: float,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams simulated call events turn-by-turn with realistic timestamps,
        speaker labels, transcript snippets, and simulated audio frequency waveforms.
        """
        persona = SUPPLIER_PERSONAS.get(supplier_id, SUPPLIER_PERSONAS["sup-apex"])
        script = persona["script_template"]

        total_steps = len(script)
        accumulated_transcript = []

        for idx, (timestamp, speaker, text) in enumerate(script):
            formatted_text = text.format(sku=sku, description=description, qty=target_qty, budget=target_budget)
            accumulated_transcript.append(f"[{speaker}] {formatted_text}")

            # Generate synthetic audio waveform amplitudes (0-100)
            waveform = [random.randint(15, 95) if speaker in ["CalleAgent", "Supplier"] else random.randint(2, 10) for _ in range(16)]

            yield {
                "event": "transcript_chunk",
                "step": idx + 1,
                "total_steps": total_steps,
                "timestamp_seconds": timestamp,
                "speaker": speaker,
                "text": formatted_text,
                "waveform": waveform,
                "full_transcript": "\n".join(accumulated_transcript),
                "is_call_active": idx < (total_steps - 1),
            }

            # Brief non-blocking async delay to simulate realistic speaking cadence
            await asyncio.sleep(0.35)

        # Yield completion event
        yield {
            "event": "call_completed",
            "supplier_id": supplier_id,
            "disposition": "quote_received",
            "duration_seconds": script[-1][0],
            "full_transcript": "\n".join(accumulated_transcript),
        }

    @staticmethod
    def get_simulated_extraction(
        rfq_id: str,
        supplier_id: str,
        sku: str,
        target_qty: int,
        target_budget: float,
    ) -> QuoteExtraction:
        """Generates the grounded structured quote for a simulated supplier."""
        persona = SUPPLIER_PERSONAS.get(supplier_id, SUPPLIER_PERSONAS["sup-apex"])
        
        # Calculate pricing
        base_unit_price = round(persona["tiers"][0][1], 2)
        total_cost = round(base_unit_price * target_qty + persona["freight_cost"], 2)

        volume_tiers = []
        for min_q, u_price in persona["tiers"]:
            savings = round(((base_unit_price - u_price) / base_unit_price) * 100, 2) if base_unit_price > 0 else 0.0
            volume_tiers.append(VolumeTier(min_quantity=min_q, unit_price=u_price, savings_percent=savings))

        # Citations
        citations = [
            GroundedCitation(
                claim=f"Base unit price for {target_qty} units is ${base_unit_price:.2f}",
                verbatim_quote=f"For {target_qty} units, our price is ${base_unit_price:.2f} each.",
                timestamp_seconds=24,
            ),
            GroundedCitation(
                claim=f"In-stock lead time is {persona['lead_time_days']} business days",
                verbatim_quote=f"We have units in stock, transit is {persona['lead_time_days']} business days.",
                timestamp_seconds=52,
            ),
            GroundedCitation(
                claim=f"Freight terms: {persona['freight_terms']}",
                verbatim_quote=f"Freight terms are {persona['freight_terms']}.",
                timestamp_seconds=56,
            ),
        ]

        return QuoteExtraction(
            rfq_id=rfq_id,
            supplier_name=persona["name"],
            call_disposition=CallDisposition.QUOTE_RECEIVED,
            representative_name=persona["rep"],
            quote_reference_number=persona["quote_ref"],
            sku_quoted=sku if not persona["substitute"] else persona["substitute"].substitute_sku,
            is_exact_match=(persona["substitute"] is None),
            stock_status=persona["stock_status"],
            lead_time_days=persona["lead_time_days"],
            base_unit_price=base_unit_price,
            currency="USD",
            volume_tiers=volume_tiers,
            freight_terms=persona["freight_terms"],
            estimated_freight_cost=persona["freight_cost"],
            substitute_offered=persona["substitute"],
            confidence_score=0.98,
            grounded_citations=citations,
            notes=persona["notes"],
        )
