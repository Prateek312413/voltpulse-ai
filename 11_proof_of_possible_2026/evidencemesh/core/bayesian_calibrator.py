"""
Bayesian Epistemic Calibration and Uncertainty Quantification Engine.
Implements conjugate Beta-Binomial belief updating, 95% credible intervals,
Expected Calibration Error (ECE), and Brier reliability scoring.
"""

import math
import numpy as np
from typing import List, Tuple
from evidencemesh.models import BayesianCalibrationResult, AtomicClaim, VerificationStatus


class BayesianCalibrator:
    """
    Quantifies subjective belief, epistemic confidence, and calibration error across claims.
    """

    def __init__(self, prior_alpha: float = 2.0, prior_beta: float = 2.0):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta

    def calibrate_claims(self, claims: List[AtomicClaim]) -> BayesianCalibrationResult:
        """
        Computes Bayesian posterior, credible intervals, and calibration metrics over a set of claims.
        """
        if not claims:
            return BayesianCalibrationResult(
                prior_alpha=self.prior_alpha,
                prior_beta=self.prior_beta,
                posterior_alpha=self.prior_alpha,
                posterior_beta=self.prior_beta,
                calibrated_probability=0.5,
                credible_interval_low_95=0.2,
                credible_interval_high_95=0.8,
                expected_calibration_error=0.0,
                brier_score=0.25,
                epistemic_entropy=1.0
            )

        # Count weighted positive (supporting) and negative (refuting) evidence units
        positive_evidence = 0.0
        negative_evidence = 0.0

        for claim in claims:
            if claim.status == VerificationStatus.VERIFIED:
                weight = sum(s.reliability_weight for s in claim.supporting_evidence) or 1.0
                positive_evidence += weight * claim.confidence_score
            elif claim.status in [VerificationStatus.REFUTED, VerificationStatus.CONTRADICTED]:
                weight = sum(s.reliability_weight for s in claim.refuting_evidence) or 1.0
                negative_evidence += weight * (1.0 - claim.confidence_score + 0.5)
            else:
                positive_evidence += 0.5
                negative_evidence += 0.5

        post_alpha = self.prior_alpha + positive_evidence
        post_beta = self.prior_beta + negative_evidence

        # Posterior Mean (calibrated probability)
        calibrated_prob = post_alpha / (post_alpha + post_beta)

        # Posterior Variance: Var(theta) = (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
        var = (post_alpha * post_beta) / (((post_alpha + post_beta) ** 2) * (post_alpha + post_beta + 1))
        std_dev = math.sqrt(var)

        # 95% Credible Interval (Normal approximation to Beta posterior for large alpha+beta, bounded [0, 1])
        ci_low = max(0.0, calibrated_prob - 1.96 * std_dev)
        ci_high = min(1.0, calibrated_prob + 1.96 * std_dev)

        # Expected Calibration Error (ECE) calculation
        ece = self._calculate_ece(claims)

        # Brier Score: 1/N sum((prob_i - y_i)^2)
        brier = self._calculate_brier(claims)

        # Epistemic Shannon Entropy: -p log2(p) - (1-p) log2(1-p)
        p = max(1e-6, min(1.0 - 1e-6, calibrated_prob))
        entropy = - (p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))

        return BayesianCalibrationResult(
            prior_alpha=round(self.prior_alpha, 3),
            prior_beta=round(self.prior_beta, 3),
            posterior_alpha=round(post_alpha, 3),
            posterior_beta=round(post_beta, 3),
            calibrated_probability=round(calibrated_prob, 4),
            credible_interval_low_95=round(ci_low, 4),
            credible_interval_high_95=round(ci_high, 4),
            expected_calibration_error=round(ece, 4),
            brier_score=round(brier, 4),
            epistemic_entropy=round(entropy, 4)
        )

    def _calculate_ece(self, claims: List[AtomicClaim], num_bins: int = 5) -> float:
        """Calculates Expected Calibration Error across confidence bins."""
        if not claims:
            return 0.0

        bins = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        n = len(claims)

        for i in range(num_bins):
            bin_lower = bins[i]
            bin_upper = bins[i + 1]

            bin_claims = [c for c in claims if bin_lower <= c.confidence_score < bin_upper or (i == num_bins - 1 and c.confidence_score == 1.0)]
            if not bin_claims:
                continue

            bin_size = len(bin_claims)
            avg_confidence = sum(c.confidence_score for c in bin_claims) / bin_size
            avg_accuracy = sum(1.0 if c.status == VerificationStatus.VERIFIED else 0.0 for c in bin_claims) / bin_size

            ece += (bin_size / n) * abs(avg_accuracy - avg_confidence)

        return float(ece)

    def _calculate_brier(self, claims: List[AtomicClaim]) -> float:
        """Calculates Brier score (mean squared error of probabilistic predictions)."""
        if not claims:
            return 0.0

        errors = []
        for c in claims:
            y = 1.0 if c.status == VerificationStatus.VERIFIED else 0.0
            errors.append((c.confidence_score - y) ** 2)

        return float(sum(errors) / len(errors))
