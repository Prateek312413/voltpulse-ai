"""
Unit Tests for Crisis NLP & Distress Triage Engine
"""

import pytest
from core.crisis_triage_nlp import CrisisNLPEngine, DistressCategory


@pytest.fixture
def nlp_engine():
    return CrisisNLPEngine()


def test_critical_medical_triage(nlp_engine):
    text = "Emergency! 72 year old diabetic grandfather is unconscious with severe bleeding. We need rapid insulin and trauma kit!"
    res = nlp_engine.analyze_message(text, triage_id="TEST-001")

    assert res.primary_category == DistressCategory.CRITICAL_MEDICAL
    assert res.urgency_score >= 8.5
    assert any("diabet" in m.lower() for m in res.entities.medical_conditions)
    assert "insulin_cold_pack" in res.entities.specific_supplies_needed
    assert "KIT-MED-INSULIN-TRAUMA" in res.recommended_kit_type


def test_swiftwater_trapped_urgency_escalation(nlp_engine):
    text = "Rising water past 2nd floor! 4 family members trapped on rooftop, drowning danger!"
    res = nlp_engine.analyze_message(text, triage_id="TEST-002")

    assert res.primary_category == DistressCategory.TRAPPED_SEARCH_RESCUE
    assert res.urgency_score >= 9.0
    assert res.entities.headcount == 4
    assert "Swiftwater Rescue" in res.suggested_responder_skills


def test_vulnerable_headcount_extraction(nlp_engine):
    text = "Shelter group with 3 babies and 2 elderly grandparents shivering from cold. Need infant formula and thermal blankets."
    res = nlp_engine.analyze_message(text, triage_id="TEST-003")

    assert res.entities.vulnerable_infants == 3
    assert res.entities.vulnerable_elderly == 2
    assert "infant_formula_diapers" in res.entities.specific_supplies_needed
    assert "thermal_blankets_tarp" in res.entities.specific_supplies_needed


def test_gps_coordinate_extraction(nlp_engine):
    text = "SOS trapped near river bank at coordinates 37.7749, -122.4194 please send boat!"
    res = nlp_engine.analyze_message(text, triage_id="TEST-004")

    assert res.entities.latitude == pytest.approx(37.7749, abs=0.001)
    assert res.entities.longitude == pytest.approx(-122.4194, abs=0.001)


def test_multilingual_distress_detection(nlp_engine):
    # Spanish
    es_text = "¡Emergencia médica! Abuela con sangrado grave y ataque cardiaco en el hospital central."
    es_res = nlp_engine.analyze_message(es_text)
    assert es_res.primary_category == DistressCategory.CRITICAL_MEDICAL
    assert es_res.urgency_score >= 8.0

    # Hindi
    hi_text = "बाढ़ का पानी छत तक पहुँच गया है, 5 लोग मलबे में फंसे हुए हैं, तत्काल मदद चाहिए!"
    hi_res = nlp_engine.analyze_message(hi_text)
    assert hi_res.primary_category == DistressCategory.TRAPPED_SEARCH_RESCUE
    assert hi_res.urgency_score >= 8.5


def test_empty_fallback(nlp_engine):
    res = nlp_engine.analyze_message("")
    assert res.primary_category == DistressCategory.GENERAL_ASSISTANCE
    assert res.urgency_score == 2.0
