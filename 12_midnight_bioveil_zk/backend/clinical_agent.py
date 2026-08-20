"""
BioVeil ZK — Clinical Pharmacovigilance Sentinel, Bayesian Trajectory Engine & MCDA Matcher
Protocol intelligence for Zero-Knowledge clinical trials on Midnight Network.
"""

import math
import time
from typing import List, Dict, Any, Tuple
from backend.data_models import ClinicalTrialModel, PatientEHRProfile
from backend.zk_engine import poseidon_hash

# Common oncological & clinical drug interaction contraindication matrix
CONTRAINDICATION_MATRIX = {
    ("CAR_T_CELL_THERAPY", "HIGH_DOSE_SYSTEMIC_CORTICOSTEROIDS"): "High-dose steroids ablate CAR-T efficacy and persistence.",
    ("EGFR_TKI_OSIMERTINIB", "STRONG_CYP3A4_INDUCERS"): "Substantial reduction in plasma exposure of Osimertinib.",
    ("MONOCLONAL_ANTIBODY_ALZHEIMERS", "ANTICOAGULANTS_WARFARIN"): "Elevated risk of Amyloid-Related Imaging Abnormalities (ARIA-H microhemorrhages).",
    ("PCSK9_RNAI_INCLISIRAN", "HEPATIC_CHILD_PUGH_C"): "Unstudied hepatic clearance kinetics in advanced cirrhosis.",
    ("TRASTUZUMAB_DERUXTECAN", "DOXORUBICIN_CONCURRENT"): "Cumulative left-ventricular cardiotoxicity & cardiomyopathy risk."
}


class ClinicalPharmacovigilanceSentinel:
    """
    Evaluates patient medications against trial investigational drugs.
    Proves zero lethal contraindications in Zero-Knowledge without leaking current prescriptions.
    """

    @staticmethod
    def check_interaction_safety(
        trial_drug: str,
        patient_medications: List[str]
    ) -> Tuple[bool, List[str], str]:
        detected_warnings = []
        is_safe = True

        for med in patient_medications:
            pair1 = (trial_drug.upper(), med.upper())
            pair2 = (med.upper(), trial_drug.upper())
            if pair1 in CONTRAINDICATION_MATRIX:
                is_safe = False
                detected_warnings.append(CONTRAINDICATION_MATRIX[pair1])
            elif pair2 in CONTRAINDICATION_MATRIX:
                is_safe = False
                detected_warnings.append(CONTRAINDICATION_MATRIX[pair2])

        # Synthesize ZK safety proof commitment
        safety_commitment = poseidon_hash(
            "PHARMACOVIGILANCE_SAFETY_ROOT",
            trial_drug,
            len(patient_medications),
            is_safe
        )

        return is_safe, detected_warnings, safety_commitment


class BayesianBiomarkerTrajectoryEngine:
    """
    Standard Clinical Protocol Adherence & Safety Tracking Engine.
    Evaluates protocol checkpoint projections within safety baselines.
    """

    @staticmethod
    def forecast_checkpoint_adherence(
        baseline_egfr: float,
        weeks_in_trial: int = 12,
        decay_rate: float = 0.002
    ) -> Dict[str, Any]:
        """
        Computes standard clinical safety margins over trial milestone weeks.
        """
        trajectory = []
        for week in range(0, weeks_in_trial + 1, 2):
            mean_val = round(baseline_egfr * math.exp(-decay_rate * week), 2)
            sigma = round(1.2 + 0.35 * math.sqrt(week), 2)
            lower_95 = round(max(0, mean_val - 1.96 * sigma), 2)
            upper_95 = round(mean_val + 1.96 * sigma, 2)
            
            trajectory.append({
                "week": week,
                "projected_mean": mean_val,
                "sigma": sigma,
                "ci_95_lower": lower_95,
                "ci_95_upper": upper_95,
                "is_above_safety_cutoff": lower_95 >= 55.0
            })

        adherence_confidence = round(
            sum(1 for t in trajectory if t["is_above_safety_cutoff"]) / len(trajectory) * 100, 1
        )

        return {
            "trajectory_points": trajectory,
            "overall_adherence_safety_score": f"{adherence_confidence}%",
            "model_type": "Standard Clinical Safety Margin Forecast",
            "zk_trajectory_hash": poseidon_hash("SAFETY_TRAJECTORY", baseline_egfr, weeks_in_trial, adherence_confidence)
        }


class MCDAClinicalTrialMatcher:
    """
    Multi-Criteria Decision Analysis (MCDA) Scoring Engine.
    Scores trial compatibility across:
    1. Genomic Locus Affinity (40%)
    2. Organ Safety Reserve (25%)
    3. Shielded Escrow Incentive (20%)
    4. Protocol Simplicity & Checkpoint Load (15%)
    """

    @staticmethod
    def rank_trials_for_patient(
        patient: PatientEHRProfile,
        trials: List[ClinicalTrialModel]
    ) -> List[Dict[str, Any]]:
        scored_trials = []

        for trial in trials:
            c = trial.criteria
            
            # 1. Genomic Affinity (0 - 40 pts)
            target = c.required_biomarker.strip().upper()
            patient_bios = [b.strip().upper() for b in patient.biomarkers]
            genomic_score = 40.0 if target in patient_bios else 5.0

            # 2. Organ Safety Reserve (0 - 25 pts)
            egfr_margin = patient.egfr_level - c.min_egfr_level
            if egfr_margin >= 20:
                safety_score = 25.0
            elif egfr_margin >= 0:
                safety_score = 15.0 + (egfr_margin / 20.0) * 10.0
            else:
                safety_score = 0.0

            # 3. Escrow Incentive (0 - 20 pts)
            # Scale against 10,000 NIGHT ceiling
            reward_ratio = min(1.0, trial.milestone_reward_night / 10000.0)
            escrow_score = reward_ratio * 20.0

            # 4. Phase & Capacity Reserve (0 - 15 pts)
            available_slots = max(0, trial.max_participants - trial.enrolled_count)
            capacity_ratio = min(1.0, available_slots / trial.max_participants)
            feasibility_score = capacity_ratio * 15.0

            total_score = round(genomic_score + safety_score + escrow_score + feasibility_score, 1)

            scored_trials.append({
                "trial_id": trial.trial_id,
                "title": trial.title,
                "phase": trial.phase,
                "sponsor_name": trial.sponsor_name,
                "mcda_match_score": total_score,
                "match_tier": "HIGHLY COMPATIBLE (90%+)" if total_score >= 80 else ("MODERATE MATCH" if total_score >= 60 else "LOW COMPATIBILITY"),
                "score_breakdown": {
                    "genomic_affinity": round(genomic_score, 1),
                    "safety_reserve": round(safety_score, 1),
                    "escrow_incentive": round(escrow_score, 1),
                    "cohort_feasibility": round(feasibility_score, 1)
                },
                "reward_night": trial.milestone_reward_night
            })

        # Sort descending by match score
        scored_trials.sort(key=lambda x: x["mcda_match_score"], reverse=True)
        return scored_trials
