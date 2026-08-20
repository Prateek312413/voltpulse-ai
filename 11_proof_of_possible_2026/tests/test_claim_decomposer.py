import pytest
from evidencemesh.core.claim_decomposer import ClaimDecomposer
from evidencemesh.models import ClaimType


def test_claim_decomposer_basic():
    decomposer = ClaimDecomposer()
    text = "Empagliflozin reduces the risk of sustained decline in eGFR by 28% in chronic kidney disease patients. The patient was prescribed Amoxicillin."
    claims = decomposer.decompose(text)

    assert len(claims) >= 2
    assert claims[0].claim_id == "CLM-001"
    assert claims[0].numerical_value == 28.0
    assert claims[0].claim_type in [ClaimType.STATISTICAL, ClaimType.CAUSAL_LINK]


def test_claim_decomposer_empty_input():
    decomposer = ClaimDecomposer()
    assert decomposer.decompose("") == []
    assert decomposer.decompose("   ") == []


def test_compound_clause_splitting():
    decomposer = ClaimDecomposer()
    text = "Cell energy density reaches 450 Wh/kg; whereas standard cells reach 260 Wh/kg."
    claims = decomposer.decompose(text)
    assert len(claims) == 2
