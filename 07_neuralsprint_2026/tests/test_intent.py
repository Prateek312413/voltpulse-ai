"""
Unit tests for AACIntentPredictor
"""
import pytest
from core.intent_agent import AACIntentPredictor

@pytest.fixture
def intent_engine():
    return AACIntentPredictor()

def test_predict_intents_empty(intent_engine):
    preds = intent_engine.predict_intents([])
    assert len(preds) > 0
    assert preds[0]["urgency"] == "MEDIUM"

def test_predict_intents_water(intent_engine):
    preds = intent_engine.predict_intents(["WATER"])
    assert len(preds) >= 2
    assert any("water" in p["phrase"].lower() for p in preds)
    assert preds[0]["confidence"] > 0.6

def test_predict_intents_critical_pain(intent_engine):
    preds = intent_engine.predict_intents(["PAIN"])
    critical_preds = [p for p in preds if p["urgency"] == "CRITICAL"]
    assert len(critical_preds) > 0
    assert critical_preds[0]["speech_pitch"] > 1.0
