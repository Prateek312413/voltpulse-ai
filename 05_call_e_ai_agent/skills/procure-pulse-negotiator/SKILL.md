---
name: procure-pulse-negotiator
description: Autonomous industrial supply chain and MRO procurement phone-call skill that executes RFQs, negotiates volume pricing tiers, confirms inventory lead times, and extracts grounded structured quotes using CALL-E without unauthorized purchasing commitments.
license: MIT
---
# ProcurePulse Negotiator

Use this skill when a procurement officer, supply chain manager, maintenance coordinator, or engineering lead has authorized an outbound phone inquiry to verify parts availability, request price quotes, explore volume discount tiers, and verify lead times from industrial suppliers, distributors, or fabricators.

The call strictly discloses its identity as an automated procurement assistant on behalf of the purchasing team, asks for exact SKU availability, inquires about quantity-based discounts, clarifies shipping/freight terms (FOB), and records all details as structured evidence. 

**Critical Safety Gate**: This skill **never** authorizes financial transactions, issues binding Purchase Orders, or discloses credit card numbers over the phone. It collects verified quotes for a human purchasing manager to review and approve.

## When To Use

Use this skill for:
- Requesting formal price quotes and stock availability for industrial components (valves, bearings, actuators, raw metals, electronic parts, fasteners).
- Checking real-time lead times (e.g. "same-day dispatch", "2-3 business days", "backordered 4 weeks").
- Exploring tiered volume pricing (e.g., unit price at 100 vs. 500 vs. 1,000 units).
- Clarifying freight/shipping methods, estimated freight costs, and FOB terms.
- Inquiring about manufacturer-approved direct substitute SKUs if the requested part is out of stock.
- Generating structured, auditable bid records grounded with timestamped verbatim citations.

## When Not To Use

Do not use this skill to:
- Issue legally binding purchase commitments, sign contracts, or approve credit card charges over the phone.
- Disclose proprietary financial records, banking details, or internal corporate budgets.
- Mislead suppliers regarding purchase intention or submit fictitious inquiries.
- Call residential numbers, unverified numbers, or numbers not listed as commercial business sales lines.
- Harass sales desks with rapid repeated calls after a quote has already been provided or declined.
- Request regulated, restricted, or hazardous materials without prior human compliance clearance.

## Required Inputs

- `rfq_id`: Unique stable identifier for the Request for Quote campaign (e.g., `RFQ-2026-0891`).
- `supplier_name`: Commercial name of the vendor (e.g., `Apex Industrial Fasteners`).
- `to_phone_e164`: Verified business phone number in E.164 format (e.g., `+18005550199`).
- `company_name`: Disclosed buyer organization name (e.g., `VoltPulse Manufacturing Corp`).
- `buyer_contact_name`: Human procurement manager responsible for this RFQ (e.g., `Alex Morgan, Procurement Lead`).
- `parts_requested`: Array of item requests with:
  - `sku`: Manufacturer or catalog part number (e.g., `SS-400-1-4`).
  - `description`: Plain text item description (e.g., `1/4 inch 316 Stainless Steel Ball Valve, 1000 PSI`).
  - `target_quantity`: Target quantity needed (e.g., `250`).
  - `target_unit_budget`: Target or ceiling price per unit in USD (e.g., `45.00`).
  - `required_delivery_date`: Expected required arrival date (e.g., `2026-09-01`).

## Optional Inputs

- `allow_substitutions`: Boolean indicating whether the agent can accept quote for an exact functional equivalent SKU if the target SKU is backordered (default: `true`).
- `volume_tier_checks`: Array of quantity tiers to inquire about (e.g., `[250, 500, 1000]`).
- `preferred_freight_terms`: Desired shipping terms (e.g., `FOB Destination, Ground`).
- `urgency_level`: `standard`, `expedited`, or `critical_outage`.
- `voicemail_allowed`: Boolean indicating if a polite callback request message should be left (default: `true`).
- `custom_notes`: Special handling or certification requirements (e.g., `Requires Material Test Report (MTR) Mill Cert 3.1`).

## Preflight Verification Checklist

Before invoking CALL-E `plan_call`:
1. Validate `to_phone_e164` matches E.164 regex pattern `^\+[1-9]\d{1,14}$`.
2. Confirm buyer organization name and contact name are populated for mandatory transparency disclosure.
3. Check target quantity is a positive integer and part specifications are unambiguous.
4. Ensure no payment credentials or trade secret pricing formulas are embedded in the prompt.

## CALL-E Goal Construction Template

When synthesizing the `goal` parameter for CALL-E:

```text
You are calling {supplier_name} on behalf of {company_name} (Procurement Team) regarding Request for Quote {rfq_id}.

Goal:
1. Greet the sales or parts desk politely and disclose: "Hello, this is an automated procurement inquiry for {company_name}'s purchasing department regarding a commercial quote for part number {parts_requested[0].sku}."
2. Inquire whether SKU {parts_requested[0].sku} ({parts_requested[0].description}) is currently in stock for immediate dispatch.
3. Ask for the current unit price for a purchase of {parts_requested[0].target_quantity} units.
4. If the price exceeds ${parts_requested[0].target_unit_budget} or to find maximum value, politely inquire: "Do you offer tiered volume pricing if we increase the order to 500 or 1,000 units?"
5. Verify the estimated lead time or dispatch timeline to zip code/facility.
6. Ask if freight is included (FOB Destination) or if freight is billed separately.
7. If the requested SKU is out of stock, ask: "Do you have an in-stock direct functional equivalent or alternative brand that meets the same specifications?" Note the alternative SKU, manufacturer, and price.
8. Before concluding, clarify: "Thank you! I am recording these details for our purchasing manager {buyer_contact_name} to review and issue the formal Purchase Order. Could I also confirm your name or quote reference number?"
9. Thank them and end the call politely.

Strict Rules:
- DO NOT commit to buying or offer credit card/payment details.
- Be concise, professional, respectful of the sales representative's time.
- If transferred or put on hold, wait patiently. If sent to voicemail, leave a brief message asking for sales to email {buyer_contact_email} referencing {rfq_id}.
```

## Structured Result Schema

The extracted quote output conforms to the following schema:

```json
{
  "rfq_id": "RFQ-2026-0891",
  "supplier_name": "Apex Industrial Fasteners",
  "call_disposition": "quote_received",
  "representative_name": "Sarah Miller",
  "quote_reference_number": "Q-88192-A",
  "sku_quoted": "SS-400-1-4",
  "is_exact_match": true,
  "stock_status": "in_stock",
  "lead_time_days": 2,
  "base_unit_price": 42.50,
  "currency": "USD",
  "volume_tiers": [
    {"min_quantity": 250, "unit_price": 42.50},
    {"min_quantity": 500, "unit_price": 38.00},
    {"min_quantity": 1000, "unit_price": 34.20}
  ],
  "freight_terms": "FOB Destination, Ground included over $500",
  "estimated_freight_cost": 0.00,
  "substitute_offered": null,
  "confidence_score": 0.98,
  "grounded_citations": [
    {
      "claim": "Unit price at 250 units is $42.50",
      "verbatim_quote": "For 250 of the SS-400s, I can do forty-two fifty each.",
      "timestamp_seconds": 38
    },
    {
      "claim": "Tier discount at 500 units is $38.00",
      "verbatim_quote": "If you bump that up to five hundred, that drops to thirty-eight even.",
      "timestamp_seconds": 54
    },
    {
      "claim": "In stock with 2-day ground shipping",
      "verbatim_quote": "We have six hundred on the shelf right now in our Dallas warehouse, can ship today for two-day arrival.",
      "timestamp_seconds": 68
    }
  ],
  "notes": "Spoke with Sarah in commercial sales. Mill test reports included at no charge."
}
```

## Dispositions

- `quote_received`: Full or partial pricing and availability data successfully collected.
- `part_unavailable`: Supplier verified they do not stock this item and have no direct substitute.
- `voicemail_left`: Sales desk was unavailable; standard callback message left.
- `callback_requested`: Supplier requested buyer call back during specific business hours.
- `refused_quote`: Supplier declined to quote over phone (e.g. requires online portal login).
- `human_transfer_needed`: Inquiry required specialized technical engineering review.
