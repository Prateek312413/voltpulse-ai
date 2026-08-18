"""
Unit tests for AudioDSP module
"""
import numpy as np
import pytest
from core.audio_dsp import AudioDSP

@pytest.fixture
def dsp():
    return AudioDSP(sample_rate=16000)

def test_normalize_audio(dsp):
    audio = np.array([-2000.0, 4000.0, 8000.0], dtype=np.float32)
    normalized = dsp.normalize_audio(audio)
    assert np.max(normalized) == pytest.approx(1.0, 1e-4)
    assert np.min(normalized) >= -1.0

def test_extract_energy_envelope(dsp):
    # 1 second of 440Hz sine wave
    t = np.linspace(0, 1.0, 16000)
    audio = (np.sin(2 * np.pi * 440 * t) * 0.8).astype(np.float32)
    envelope = dsp.extract_energy_envelope(audio)
    assert len(envelope) > 0
    assert np.mean(envelope) > 0.1

def test_spectral_subtraction_denoise(dsp):
    t = np.linspace(0, 0.5, 8000)
    clean_signal = np.sin(2 * np.pi * 500 * t)
    noise = np.random.normal(0, 0.2, len(t))
    noisy_signal = clean_signal + noise

    denoised, snr_gain = dsp.spectral_subtraction_denoise(noisy_signal)
    assert len(denoised) == len(noisy_signal)
    assert snr_gain >= 0.0

def test_extract_formants(dsp):
    t = np.linspace(0, 0.2, 3200)
    audio = np.sin(2 * np.pi * 700 * t) + 0.5 * np.sin(2 * np.pi * 1600 * t)
    formants = dsp.extract_formants(audio, max_formants=3)
    assert len(formants) == 3
    assert formants[0]["formant"] == "F1"
    assert formants[0]["frequency_hz"] > 0

def test_compute_spectral_features(dsp):
    t = np.linspace(0, 0.2, 3200)
    audio = np.sin(2 * np.pi * 800 * t)
    feats = dsp.compute_spectral_features(audio)
    assert "centroid_hz" in feats
    assert "clarity_score" in feats
    assert 0.0 <= feats["clarity_score"] <= 1.0
