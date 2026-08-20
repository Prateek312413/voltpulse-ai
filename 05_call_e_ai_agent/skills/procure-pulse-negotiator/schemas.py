"""
Pydantic Schemas for ProcurePulse AI (CALL-E Integration)
Defines strictly typed request, extraction, evaluation, and PO data structures.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class CallDisposition(str, Enum):
    QUOTE_RECEIVED = "quote_received"
    PART_UNAVAILABLE = "part_unavailable"
    VOICEMAIL_LEFT = "voicemail_left"
    CALLBACK_REQUESTED = "callback_requested"
    REFUSED_QUOTE = "refused_quote"
    HUMAN_TRANSFER_NEEDED = "human_transfer_needed"
    FAILED_CALL = "failed_call"


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    BACKORDERED = "backordered"
    DISCONTINUED = "discontinued"
    UNKNOWN = "unknown"


class VolumeTier(BaseModel):
    min_quantity: int = Field(..., ge=1, description="Minimum quantity for this price tier")
    unit_price: float = Field(..., ge=0.0, description="Price per unit in USD at this volume")
    savings_percent: Optional[float] = Field(default=0.0, description="Percentage savings relative to baseline unit price")


class GroundedCitation(BaseModel):
    claim: str = Field(..., description="The structured fact or figure extracted")
    verbatim_quote: str = Field(..., description="Exact word-for-word transcript snippet supporting this claim")
    timestamp_seconds: Optional[int] = Field(default=0, ge=0, description="Timestamp offset in seconds from start of call")


class SubstitutePart(BaseModel):
    substitute_sku: str = Field(..., description="Alternative part or manufacturer number offered")
    manufacturer: Optional[str] = Field(default=None, description="Manufacturer of substitute part")
    description: Optional[str] = Field(default=None, description="Description and specification of substitute")
    unit_price: float = Field(..., ge=0.0, description="Quoted unit price for substitute")
    spec_compatibility: Optional[str] = Field(default="Direct Form-Fit-Function Drop-in Replacement")


class RequestedPart(BaseModel):
    sku: str = Field(..., min_length=1, description="Part number or SKU")
    description: str = Field(..., min_length=1, description="Description of the item")
    target_quantity: int = Field(..., ge=1, description="Quantity required")
    target_unit_budget: float = Field(..., gt=0.0, description="Ceiling budget per unit in USD")
    required_delivery_date: Optional[str] = Field(default=None, description="ISO date YYYY-MM-DD")


class ProcurementCallGoal(BaseModel):
    rfq_id: str = Field(..., description="Unique RFQ ID")
    supplier_name: str = Field(..., description="Vendor name")
    to_phone_e164: str = Field(..., description="E.164 phone number e.g. +18005550199")
    company_name: str = Field(default="VoltPulse Manufacturing Corp", description="Disclosed buying entity")
    buyer_contact_name: str = Field(default="Alex Morgan", description="Human procurement lead")
    buyer_contact_email: str = Field(default="procurement@voltpulse.ai", description="Contact email for quotes")
    parts_requested: List[RequestedPart] = Field(..., min_length=1)
    allow_substitutions: bool = Field(default=True)
    volume_tier_checks: List[int] = Field(default_factory=lambda: [250, 500, 1000])
    preferred_freight_terms: str = Field(default="FOB Destination, Ground")
    urgency_level: str = Field(default="standard")
    voicemail_allowed: bool = Field(default=True)
    custom_notes: Optional[str] = Field(default=None)

    @field_validator("to_phone_e164")
    @classmethod
    def validate_e164(cls, v: str) -> str:
        v = v.strip()
        pattern = r"^\+[1-9]\d{1,14}$"
        if not re.match(pattern, v):
            raise ValueError(f"Phone number '{v}' is not a valid E.164 format (e.g. +18005550199)")
        return v

    def to_calle_prompt(self) -> str:
        """Synthesizes the strict, high-converting goal string for CALL-E plan_call."""
        part = self.parts_requested[0]
        tiers_str = ", ".join(str(t) for t in self.volume_tier_checks)
        
        prompt = (
            f"You are calling {self.supplier_name} on behalf of {self.company_name} "
            f"regarding Request for Quote #{self.rfq_id}.\n\n"
            f"Goal:\n"
            f"1. Greet the sales or parts desk politely and disclose: "
            f"'Hello, this is an automated inquiry on behalf of {self.company_name}'s procurement team "
            f"regarding a commercial price and availability quote for part number {part.sku}.'\n"
            f"2. Inquire whether SKU {part.sku} ({part.description}) is currently in stock for immediate dispatch.\n"
            f"3. Ask for their current commercial unit price for a batch order of {part.target_quantity} units.\n"
            f"4. If unit price exceeds ${part.target_unit_budget:.2f} or to find better volume tiers, ask: "
            f"'Do you offer tiered discounts if we increase the order to {tiers_str} units?'\n"
            f"5. Check estimated dispatch lead time and shipping transit time.\n"
            f"6. Ask if freight is included (FOB Destination) or billed separately.\n"
        )
        if self.allow_substitutions:
            prompt += (
                f"7. If {part.sku} is out of stock, ask: 'Do you have an in-stock direct equivalent "
                f"or alternative brand with identical specifications?' Capture alternative SKU and price.\n"
            )
        prompt += (
            f"8. Clarify: 'Thank you! I will record this quote for our procurement manager {self.buyer_contact_name} "
            f"to review and confirm the Purchase Order. Could I also confirm your name or quote reference ID?'\n"
            f"9. Thank them and conclude the call.\n\n"
            f"Strict Safety Rules:\n"
            f"- DO NOT commit to purchasing or provide any payment/credit card details.\n"
            f"- Keep dialogue professional, concise, and respectful.\n"
            f"- If sent to voicemail, leave a brief message asking sales to email {self.buyer_contact_email} with quote for {part.sku} referencing RFQ {self.rfq_id}."
        )
        return prompt


class QuoteExtraction(BaseModel):
    rfq_id: str
    supplier_name: str
    call_disposition: CallDisposition
    representative_name: Optional[str] = Field(default="Sales Desk")
    quote_reference_number: Optional[str] = Field(default=None)
    sku_quoted: str
    is_exact_match: bool = Field(default=True)
    stock_status: StockStatus = Field(default=StockStatus.IN_STOCK)
    lead_time_days: int = Field(default=3, ge=0)
    base_unit_price: float = Field(..., ge=0.0)
    currency: str = Field(default="USD")
    volume_tiers: List[VolumeTier] = Field(default_factory=list)
    freight_terms: str = Field(default="FOB Destination")
    estimated_freight_cost: float = Field(default=0.0, ge=0.0)
    substitute_offered: Optional[SubstitutePart] = Field(default=None)
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    grounded_citations: List[GroundedCitation] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)


class SupplierBidResult(BaseModel):
    supplier_id: str
    supplier_name: str
    phone_number: str
    supplier_rating: float = Field(default=4.5, ge=1.0, le=5.0)
    quote: Optional[QuoteExtraction] = None
    mcda_score: float = Field(default=0.0, ge=0.0, le=100.0)
    rank: int = Field(default=1)
    is_recommended: bool = Field(default=False)
    total_cost_at_target_qty: float = Field(default=0.0)
    potential_savings: float = Field(default=0.0)
    savings_percent: float = Field(default=0.0)
    call_duration_seconds: int = Field(default=0)
    call_started_at: Optional[str] = None
    call_completed_at: Optional[str] = None
    transcript: Optional[str] = None
