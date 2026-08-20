"""
ProcurePulse Multi-Criteria Decision Analysis (MCDA) Ranking Engine
Evaluates supplier bids across price, lead-time, supplier rating, freight terms, and volume flexibility.
"""

from typing import List, Dict, Any
from skills.procure_pulse_negotiator.schemas import SupplierBidResult, QuoteExtraction


class RankingEngine:
    """Ranks supplier bids using Multi-Criteria Decision Analysis."""

    # Default MCDA Criterion Weights (sum to 1.0)
    WEIGHT_PRICE = 0.45
    WEIGHT_LEAD_TIME = 0.25
    WEIGHT_RATING = 0.15
    WEIGHT_FREIGHT = 0.10
    WEIGHT_TIER_FLEXIBILITY = 0.05

    @classmethod
    def rank_bids(
        cls,
        bids: List[SupplierBidResult],
        target_qty: int,
        target_unit_budget: float,
    ) -> List[SupplierBidResult]:
        """
        Evaluates and ranks a collection of supplier bids.
        Sets mcda_score, rank, potential_savings, and is_recommended flag.
        """
        if not bids:
            return []

        scored_bids = []

        # Find min and max values across the batch for proportional normalization
        valid_bids = [b for b in bids if b.quote is not None]
        if not valid_bids:
            return bids

        min_price = min(b.quote.base_unit_price for b in valid_bids)
        max_price = max(b.quote.base_unit_price for b in valid_bids) or 1.0
        min_lead = min(b.quote.lead_time_days for b in valid_bids)
        max_lead = max(b.quote.lead_time_days for b in valid_bids) or 1.0

        for bid in bids:
            if not bid.quote:
                bid.mcda_score = 0.0
                bid.rank = len(bids)
                bid.is_recommended = False
                continue

            quote = bid.quote
            unit_price = quote.base_unit_price
            total_batch_cost = round(unit_price * target_qty + quote.estimated_freight_cost, 2)
            budget_total = round(target_unit_budget * target_qty, 2)
            dollar_savings = round(budget_total - total_batch_cost, 2)
            savings_pct = round((dollar_savings / budget_total) * 100, 2) if budget_total > 0 else 0.0

            bid.total_cost_at_target_qty = total_batch_cost
            bid.potential_savings = max(0.0, dollar_savings)
            bid.savings_percent = max(0.0, savings_pct)

            # 1. Price Score (0 - 100) -> Lower price = higher score
            if max_price == min_price:
                price_score = 100.0
            else:
                price_score = 100.0 * (1.0 - (unit_price - min_price) / (max_price - min_price + 1e-5))

            # 2. Lead Time Score (0 - 100) -> Shorter lead time = higher score
            if max_lead == min_lead:
                lead_score = 100.0
            else:
                lead_score = 100.0 * (1.0 - (quote.lead_time_days - min_lead) / (max_lead - min_lead + 1e-5))

            # 3. Rating Score (0 - 100)
            rating_score = (bid.supplier_rating / 5.0) * 100.0

            # 4. Freight Score (0 - 100)
            freight_score = 100.0 if quote.estimated_freight_cost == 0.0 else 50.0

            # 5. Volume Tier Flexibility (0 - 100)
            tier_score = min(100.0, len(quote.volume_tiers) * 33.3)

            # Composite Weighted MCDA Score
            mcda_composite = (
                cls.WEIGHT_PRICE * price_score
                + cls.WEIGHT_LEAD_TIME * lead_score
                + cls.WEIGHT_RATING * rating_score
                + cls.WEIGHT_FREIGHT * freight_score
                + cls.WEIGHT_TIER_FLEXIBILITY * tier_score
            )

            bid.mcda_score = round(mcda_composite, 1)
            scored_bids.append(bid)

        # Sort descending by MCDA score
        scored_bids.sort(key=lambda b: b.mcda_score, reverse=True)

        # Assign ranks and mark #1 as recommended
        for idx, b in enumerate(scored_bids):
            b.rank = idx + 1
            b.is_recommended = (idx == 0)

        return scored_bids
