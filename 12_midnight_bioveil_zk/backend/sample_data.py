"""
Sample Synthetic Clinical Trials & Patient Datasets for BioVeil ZK
"""

import time
import secrets
from typing import List, Dict
from backend.data_models import (
    ClinicalTrialModel,
    EligibilityCriteriaModel,
    PatientEHRProfile,
    TrialStatusEnum
)
from backend.zk_engine import compute_biomarker_hash, compute_condition_mask


def get_initial_trials() -> List[ClinicalTrialModel]:
    now = int(time.time())

    her2_hash = compute_biomarker_hash("HER2_POS_EXON20")
    egfr_hash = compute_biomarker_hash("EGFR_T790M_MUTATION")
    apoe_hash = compute_biomarker_hash("APOE4_HOMOZYGOUS")
    pcsk9_hash = compute_biomarker_hash("PCSK9_GAIN_OF_FUNCTION")

    trials = [
        ClinicalTrialModel(
            trial_id="0x4f8a1290bb34c980a421c002fa883901bca7290192e482710492817290184a21",
            title="Targeted HER2+ Exon 20 CAR-T Oncology Protocol (Phase IIb)",
            sponsor_name="Genentech Oncology & Dana-Farber Cancer Institute",
            sponsor_address="midnight1q_sponsor_genentech_89a01f9",
            phase="Phase IIb",
            therapeutic_area="Oncology",
            description=(
                "Evaluating next-generation selective CAR-T cell infusion targeting HER2+ refractory "
                "metastatic malignancies with autonomous zero-knowledge patient safety monitoring."
            ),
            criteria=EligibilityCriteriaModel(
                min_age=21,
                max_age=65,
                required_biomarker="HER2_POS_EXON20",
                required_biomarker_hash=her2_hash,
                min_egfr_level=60,
                max_blood_pressure_systolic=140,
                excluded_conditions=[
                    "ACTIVE_MALIGNANCY_OTHER",
                    "END_STAGE_RENAL_DISEASE",
                    "PREVIOUS_IMMUNOTHERAPY_TOXICITY"
                ],
                excluded_conditions_mask=compute_condition_mask([
                    "ACTIVE_MALIGNANCY_OTHER",
                    "END_STAGE_RENAL_DISEASE",
                    "PREVIOUS_IMMUNOTHERAPY_TOXICITY"
                ])
            ),
            status=TrialStatusEnum.ACTIVE,
            max_participants=50,
            enrolled_count=18,
            escrow_deposit_night=250000,
            milestone_reward_night=5000,
            creation_timestamp=now - (86400 * 12),
            contract_address="midnight1q_bioveil_zk_c4109fa8"
        ),
        ClinicalTrialModel(
            trial_id="0x7b22109849204018239019248019284019284019284019283019283019283019",
            title="EGFR T790M Non-Small Cell Lung Cancer mRNA Immunotherapy",
            sponsor_name="BioNTech & Memorial Sloan Kettering",
            sponsor_address="midnight1q_sponsor_biontech_44e9081",
            phase="Phase III",
            therapeutic_area="Immuno-Oncology",
            description=(
                "Pioneering individualized mRNA neoantigen vaccine therapy for advanced NSCLC harboring "
                "EGFR T790M resistance mutations with shielded patient milestone stipends."
            ),
            criteria=EligibilityCriteriaModel(
                min_age=25,
                max_age=72,
                required_biomarker="EGFR_T790M_MUTATION",
                required_biomarker_hash=egfr_hash,
                min_egfr_level=55,
                max_blood_pressure_systolic=145,
                excluded_conditions=[
                    "ACTIVE_AUTOIMMUNE_DISEASE",
                    "HEPATIC_IMPAIRMENT_CHILD_PUGH_C"
                ],
                excluded_conditions_mask=compute_condition_mask([
                    "ACTIVE_AUTOIMMUNE_DISEASE",
                    "HEPATIC_IMPAIRMENT_CHILD_PUGH_C"
                ])
            ),
            status=TrialStatusEnum.ACTIVE,
            max_participants=100,
            enrolled_count=42,
            escrow_deposit_night=600000,
            milestone_reward_night=6000,
            creation_timestamp=now - (86400 * 20),
            contract_address="midnight1q_bioveil_zk_c4109fa8"
        ),
        ClinicalTrialModel(
            trial_id="0x9910c28301948201948201948201948201948201948201948201948201948201",
            title="APOE-ε4 Early-Onset Alzheimer's Neuroprotection Trial",
            sponsor_name="Biogen & Harvard Brain Initiative",
            sponsor_address="midnight1q_sponsor_biogen_11a882c",
            phase="Phase IIa",
            therapeutic_area="Neurology",
            description=(
                "Investigating brain-penetrant monoclonal antibody cocktail for slowing amyloid aggregation "
                "in high-risk asymptomatic APOE-ε4 carriers under zero-knowledge HIPAA compliance."
            ),
            criteria=EligibilityCriteriaModel(
                min_age=45,
                max_age=70,
                required_biomarker="APOE4_HOMOZYGOUS",
                required_biomarker_hash=apoe_hash,
                min_egfr_level=60,
                max_blood_pressure_systolic=135,
                excluded_conditions=[
                    "SEVERE_CARDIAC_ARRHYTHMIA",
                    "ACTIVE_MALIGNANCY_OTHER"
                ],
                excluded_conditions_mask=compute_condition_mask([
                    "SEVERE_CARDIAC_ARRHYTHMIA",
                    "ACTIVE_MALIGNANCY_OTHER"
                ])
            ),
            status=TrialStatusEnum.ACTIVE,
            max_participants=40,
            enrolled_count=12,
            escrow_deposit_night=320000,
            milestone_reward_night=8000,
            creation_timestamp=now - (86400 * 5),
            contract_address="midnight1q_bioveil_zk_c4109fa8"
        ),
        ClinicalTrialModel(
            trial_id="0x3348109284019284019284019284019284019284019284019284019284019284",
            title="PCSK9-Resistant Hypercholesterolemia CRISPR RNA-i Protocol",
            sponsor_name="Novartis Cardiovascular & Oxford Heart Centre",
            sponsor_address="midnight1q_sponsor_novartis_77019aa",
            phase="Phase I/II",
            therapeutic_area="Cardiovascular",
            description=(
                "Targeted epigenetic silencing of hepatic PCSK9 expression in refractory hyperlipidemia "
                "with automated smart contract milestone disbursement upon verified lipid panel check-in."
            ),
            criteria=EligibilityCriteriaModel(
                min_age=18,
                max_age=60,
                required_biomarker="PCSK9_GAIN_OF_FUNCTION",
                required_biomarker_hash=pcsk9_hash,
                min_egfr_level=65,
                max_blood_pressure_systolic=140,
                excluded_conditions=[
                    "HEPATIC_IMPAIRMENT_CHILD_PUGH_C",
                    "PREGNANCY_OR_BREASTFEEDING"
                ],
                excluded_conditions_mask=compute_condition_mask([
                    "HEPATIC_IMPAIRMENT_CHILD_PUGH_C",
                    "PREGNANCY_OR_BREASTFEEDING"
                ])
            ),
            status=TrialStatusEnum.ACTIVE,
            max_participants=30,
            enrolled_count=8,
            escrow_deposit_night=150000,
            milestone_reward_night=5000,
            creation_timestamp=now - (86400 * 2),
            contract_address="midnight1q_bioveil_zk_c4109fa8"
        )
    ]
    return trials


def get_sample_patients() -> Dict[str, PatientEHRProfile]:
    return {
        "elena_vance_eligible_oncology": PatientEHRProfile(
            patient_id="PATIENT_EV_94821",
            full_name="Elena Vance",
            age=44,
            gender="Female",
            biomarkers=["HER2_POS_EXON20", "BRCA1_WILDTYPE", "PD_L1_POSITIVE"],
            egfr_level=92,
            systolic_bp=122,
            diastolic_bp=78,
            diagnosed_conditions=["STAGE_II_BREAST_CARCINOMA"],
            secret_key_hex="0x9f8812c401928401928401928401928401928401928401928401928401928401",
            midnight_shielded_address="midnight1z_shielded_patient_elena_vance_88019a"
        ),
        "marcus_chen_ineligible_age": PatientEHRProfile(
            patient_id="PATIENT_MC_11029",
            full_name="Marcus Chen",
            age=74,  # Over max age 65
            gender="Male",
            biomarkers=["HER2_POS_EXON20"],
            egfr_level=80,
            systolic_bp=128,
            diastolic_bp=82,
            diagnosed_conditions=[],
            secret_key_hex="0x1188334401928401928401928401928401928401928401928401928401928402",
            midnight_shielded_address="midnight1z_shielded_patient_marcus_chen_55219b"
        ),
        "sarah_jenkins_ineligible_renal": PatientEHRProfile(
            patient_id="PATIENT_SJ_44810",
            full_name="Sarah Jenkins",
            age=39,
            gender="Female",
            biomarkers=["HER2_POS_EXON20"],
            egfr_level=42,  # Below renal baseline 60
            systolic_bp=135,
            diastolic_bp=88,
            diagnosed_conditions=["CHRONIC_KIDNEY_DISEASE_STAGE_3"],
            secret_key_hex="0x7766554401928401928401928401928401928401928401928401928401928403",
            midnight_shielded_address="midnight1z_shielded_patient_sarah_jenkins_77192c"
        ),
        "david_rossi_eligible_lung": PatientEHRProfile(
            patient_id="PATIENT_DR_88291",
            full_name="David Rossi",
            age=52,
            gender="Male",
            biomarkers=["EGFR_T790M_MUTATION", "KRAS_WILDTYPE"],
            egfr_level=88,
            systolic_bp=126,
            diastolic_bp=80,
            diagnosed_conditions=["NON_SMALL_CELL_LUNG_CANCER"],
            secret_key_hex="0x3322110001928401928401928401928401928401928401928401928401928404",
            midnight_shielded_address="midnight1z_shielded_patient_david_rossi_33910d"
        ),
        "clara_oswald_eligible_alzheimers": PatientEHRProfile(
            patient_id="PATIENT_CO_77201",
            full_name="Dr. Clara Oswald",
            age=58,
            gender="Female",
            biomarkers=["APOE4_HOMOZYGOUS", "TREM2_NORMAL"],
            egfr_level=85,
            systolic_bp=120,
            diastolic_bp=75,
            diagnosed_conditions=["MILD_COGNITIVE_DECLINE_STAGE_1"],
            secret_key_hex="0x5544332201928401928401928401928401928401928401928401928401928405",
            midnight_shielded_address="midnight1z_shielded_patient_clara_oswald_66190e"
        )
    }
