"""
Benchmark Scenarios for EvidenceMesh.
Demonstrates multi-domain causal verification across:
1. Clinical Trials & Pharmacovigilance (AegisMed)
2. Solid-State Battery & Thermal Runaway Micro-Short (VoltPulse AI)
3. AWS Trainium2 NKI Custom Kernel Acceleration (NeuronFrontier-LM)
4. Symbolic Mathematical Verification & Wolfram Oracles (SynapseFlow)
5. Assistive AAC Acoustic Speech Restoration (NeuroAccess AI)
6. Corporate ESG Scope 1-3 Carbon Accounting
"""

from typing import List, Dict
from evidencemesh.models import Scenario


BENCHMARK_SCENARIOS: List[Scenario] = [
    Scenario(
        id="SCENARIO-CLINICAL-01",
        title="Clinical Trial Renal Protection & Allergy Shield",
        category="Biomedical & Pharmacovigilance (AegisMed)",
        description="Verifies clinical claims regarding Empagliflozin SGLT2 renal protection while cross-examining fatal penicillin anaphylaxis cross-reactivity.",
        sample_text=(
            "Empagliflozin reduces the risk of sustained decline in eGFR by 28% in chronic kidney disease patients. "
            "Because of this renal benefit, the patient was prescribed Amoxicillin for an acute sinus infection; "
            "however, the patient has a documented severe IgE-mediated anaphylactic reaction to penicillin."
        ),
        ground_truth_context="Empagliflozin 28% eGFR decline reduction is verified in Phase III trials. However, Amoxicillin is a beta-lactam and is directly contraindicated in penicillin-allergic patients."
    ),
    Scenario(
        id="SCENARIO-ENERGY-02",
        title="Solid-State Battery 450 Wh/kg Energy Density & Thermal Limits",
        category="Clean Energy & Electrochemistry (VoltPulse AI)",
        description="Audits high-density solid-state battery specifications against interfacial impedance and fast-charging physics.",
        sample_text=(
            "Our new sulfide-based solid-state battery cell achieves 450 Wh/kg gravimetric energy density at 25°C. "
            "It maintains 85% capacity retention after 800 charge cycles under 5 MPa stack pressure. "
            "Furthermore, it can be ultra-fast charged at 4C indefinitely without any thermal management or impedance degradation."
        ),
        ground_truth_context="450 Wh/kg energy density and 800 cycles at 5 MPa are experimentally verified in Nature Materials. However, the claim that 4C fast charging requires no thermal management is refuted."
    ),
    Scenario(
        id="SCENARIO-SILICON-03",
        title="AWS Trainium2 NKI Tiled FlashAttention & Muon Optimizer",
        category="AI Silicon & Kernel Engineering (NeuronFrontier-LM)",
        description="Validates hardware memory bounds (O(N) vs O(N^2) SBUF tiling) and 5th-order Newton-Schulz Muon convergence.",
        sample_text=(
            "Trainium2 TensorEngine utilizes 128x128 systolic execution tiles with 24MB on-chip SBUF SRAM. "
            "Tiled FlashAttention reduces attention memory complexity from O(N^2) to O(N) by caching softmax statistics in SBUF. "
            "The Muon optimizer applies 5th-order Newton-Schulz matrix iterations, reducing training steps to reach 1.80 val_bpb by 32%."
        ),
        ground_truth_context="All Trainium2 architectural parameters, O(N) memory complexity, and Muon 32% step reductions are verified by AWS whitepapers and empirical speedrun benchmarks."
    ),
    Scenario(
        id="SCENARIO-MATH-04",
        title="Symbolic Mathematical Proofs & CAS Dimensional Consistency",
        category="Symbolic Computation & Oracles (SynapseFlow)",
        description="Verifies the integration of generative LLMs with deterministic Computer Algebra Systems to eliminate mathematical hallucinations.",
        sample_text=(
            "Stochastic neural language models fail on multi-step symbolic integration in 41.2% of benchmark cases. "
            "Coupling generative LLMs with deterministic Computer Algebra Systems guarantees 100% algebraic and dimensional unit consistency."
        ),
        ground_truth_context="Empirically verified by Wolfram Research benchmarks and symbolic theorem provers."
    ),
    Scenario(
        id="SCENARIO-ACCESSIBILITY-05",
        title="Assistive Dysarthric Speech Phoneme Restoration & AAC",
        category="Assistive AI & Neuro-Adaptive (NeuroAccess AI)",
        description="Validates acoustic DSP spectral subtraction and LPC formant reconstruction for ALS and stroke patient speech.",
        sample_text=(
            "Spectral subtraction denoising paired with Linear Predictive Coding (LPC) formant tracking restores dysarthric acoustic speech to intelligible phonemes with 91.4% word error rate reduction across ALS cohorts."
        ),
        ground_truth_context="Verified by IEEE Transactions on Neural Systems and Rehabilitation Engineering."
    ),
    Scenario(
        id="SCENARIO-ESG-06",
        title="Corporate Net-Zero Carbon Neutrality & Scope 1-3 Audit",
        category="ESG & Climate Regulatory",
        description="Verifies GHG Scope 1-3 emissions accounting claims under ISO 14064 guidelines.",
        sample_text=(
            "The corporation achieved net-zero Scope 1 emissions by purchasing unbundled Renewable Energy Certificates (RECs). "
            "Scope 3 upstream supply chain emissions require third-party Life Cycle Assessments compliant with ISO 14064."
        ),
        ground_truth_context="Under GHG Protocol, RECs apply strictly to Scope 2 electricity consumption and do not offset Scope 1 direct combustion emissions."
    )
]


def get_scenario_by_id(scenario_id: str) -> Scenario:
    for sc in BENCHMARK_SCENARIOS:
        if sc.id == scenario_id:
            return sc
    return BENCHMARK_SCENARIOS[0]
