# Industrial Procurement Negotiation Playbook

This reference provides negotiation domain knowledge and conversational strategies used by ProcurePulse AI agents when interfacing with industrial hardware distributors, metal fabricators, and MRO parts suppliers.

## 1. Commercial Pricing Dynamics in Wholesale Supply

### Price Discovery & Markup Structure
- **List Price / Catalog Price**: High baseline MSRP; typically has 25% to 45% distributor gross margin built in.
- **Contractor / Commercial Tier**: Standard 10-15% discount granted upon disclosing a corporate or industrial entity name.
- **Volume Quantity Breaks**: Significant price cliffs commonly occur at $250, $500, $1,000, and $5,000 unit thresholds.
- **Overstock / Surplus Inquiries**: If a distributor has aging inventory in regional warehouses, sales desks frequently have leeway to discount an additional 5-8% to move stock.

## 2. Freight & Logistics Terminology (Incoterms / FOB)

- **FOB Destination (Freight Prepaid)**: The supplier pays for shipping and retains risk of loss until delivery at the buyer's loading dock. Highly preferred for standard procurement.
- **FOB Origin / Shipping Point**: The buyer pays freight charges and assumes liability once the shipment leaves the vendor's dock.
- **Lead Time Categorization**:
  - *Same-Day / Shelf Stock*: Ships within 24 hours.
  - *Factory Transfer*: 2-4 business days (transfer from central hub).
  - *MTO (Made to Order)*: 2-6 weeks manufacturing queue.

## 3. Disclosures and Consent Guidelines

Every CALL-E outbound call must adhere to commercial transparency standards:
1. **Immediate Identity Disclosure**: Introduce the agent as an automated inquiry on behalf of the specific buyer company.
2. **Clear Purpose**: State part number and estimated quantity immediately so the parts clerk can enter the SKU into their ERP/Inventory system.
3. **Strict Non-Binding Stance**: Maintain explicit boundary that this call is for quote collection and verification, while the human procurement officer issues the final PO.

## 4. Substitution Evaluation Hierarchy

When the primary part is unavailable:
1. **OEM Direct Equivalent**: Exact same specification from an approved equivalent manufacturer (e.g., Parker Hannifin vs. Swagelok valve).
2. **Superior Material Grade**: Offering 316 Stainless Steel when 304 was requested at equal or lower price.
3. **Pressure/Temperature Rating Match**: Ensuring all critical tolerance, PSI, and threading specifications match.
