"""
Benchmark Scenarios for EvidenceMesh.
Demonstrates multi-domain causal verification across clinical, energy, AI security, and regulatory compliance claims.
"""

from typing import List, Dict
from evidencemesh.models import Scenario


BENCHMARK_SCENARIOS: List[Scenario] = [
    Scenario(
        id="SCENARIO-CLINICAL-01",
        title="Clinical Trial Renal Protection & Contraindication",
        category="Biomedical & Healthcare",
        description="Verifies clinical claims regarding Empagliflozin SGLT2 inhibitor renal protection while cross-examining beta-lactam allergy safety.",
        sample_text=(
            "Empagliflozin reduces the risk of sustained decline in eGFR by 28% in chronic kidney disease patients. "
            "Because of this renal benefit, the patient was prescribed Amoxicillin for an acute sinus infection; "
            "however, the patient has a documented severe IgE-mediated anaphylactic reaction to penicillin."
        ),
        ground_truth_context="Empagliflozin 28% eGFR decline reduction is verified in Phase III trials. However, Amoxicillin is a beta-lactam and is directly contraindicated in penicillin-allergic patients."
    ),
    Scenario(
        id="SCENARIO-ENERGY-02",
        title="Solid-State Battery 450 Wh/kg Energy Density & Cycle Life",
        category="Clean Energy & Materials",
        description="Audits high-density solid-state battery specifications against interfacial impedance physics.",
        sample_text=(
            "Our new sulfide-based solid-state battery cell achieves 450 Wh/kg gravimetric energy density at 25°C. "
            "It maintains 85% capacity retention after 800 charge cycles under 5 MPa stack pressure. "
            "Furthermore, it can be ultra-fast charged at 4C indefinitely without any thermal management or impedance degradation."
        ),
        ground_truth_context="450 Wh/kg energy density and 800 cycles at 5 MPa are experimentally verified in Nature Materials. However, the claim that 4C fast charging requires no thermal management is refuted."
    ),
    Scenario(
        id="SCENARIO-AI-SECURITY-03",
        title="Autonomous AI Code Synthesis Safety & Dependency Audit",
        category="AI Systems & Cybersecurity",
        description="Assesses AI code generation safety claims against hallucinated dependencies and OWASP standards.",
        sample_text=(
            "Our autonomous AI developer tool synthesizes production software with 100% bug-free code. "
            "Standard LLM code generation generates vulnerable dependencies in 18.4% of benchmark repositories. "
            "Multi-agent cross-examination reduces hallucinated package imports by 92%."
        ),
        ground_truth_context="18.4% vulnerable package import rate and 92% multi-agent reduction are verified by arXiv:2501.08942. The 100% bug-free claim is refuted."
    ),
    Scenario(
        id="SCENARIO-ESG-04",
        title="Corporate Net-Zero Carbon Neutrality Audit",
        category="ESG & Climate Regulatory",
        description="Verifies GHG Scope 1-3 emissions accounting claims under ISO 14064 guidelines.",
        sample_text=(
            "The corporation achieved net-zero Scope 1 emissions by purchasing unbundled Renewable Energy Certificates (RECs). "
            "Scope 3 upstream supply chain emissions require third-party Life Cycle Assessments compliant with ISO 14064."
        ),
        ground_truth_context="Under GHG Protocol, RECs do not offset Scope 1 direct combustion emissions, leading to a refutation of the first claim."
    )
]


def get_scenario_by_id(scenario_id: str) -> Scenario:
    for sc in BENCHMARK_SCENARIOS:
        if sc.id == scenario_id:
            return sc
    return BENCHMARK_SCENARIOS[0]
