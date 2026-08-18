"""
Unit tests for PhonemeRestorationEngine
"""
import numpy as np
import pytest
from core.phoneme_recognizer import PhonemeRestorationEngine

@pytest.fixture
def recognizer():
    return PhonemeRestorationEngine(sample_rate=16000)

def test_phonetic_distance_exact(recognizer):
    seq = ["HH", "EH", "L", "P"]
    dist = recognizer._levenshtein_phonetic_distance(seq, seq)
    assert dist == 0.0

def test_phonetic_distance_dysarthric_substitution(recognizer):
    # D vs T has lower substitution penalty
    dist_dysarthric = recognizer._levenshtein_phonetic_distance(["D", "AA", "K"], ["T", "AA", "K"])
    dist_unrelated = recognizer._levenshtein_phonetic_distance(["Z", "AA", "K"], ["T", "AA", "K"])
    assert dist_dysarthric < dist_unrelated

def test_restore_dysarthric_transcript_from_hint(recognizer):
    res = recognizer.restore_dysarthric_transcript(raw_text_hint="wtr")
    assert res["restored_word"] == "WATER"
    assert res["confidence_score"] > 0.5
    assert len(res["phoneme_sequence"]) > 0

def test_restore_dysarthric_transcript_from_phonemes(recognizer):
    res = recognizer.restore_dysarthric_transcript(input_phonemes=["HH", "EH", "L", "P"])
    assert res["restored_word"] == "HELP"
    assert res["confidence_score"] > 0.7
