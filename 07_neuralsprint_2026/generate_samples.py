"""
Generate sample clinical audio WAV files for offline demoing in NeuroAccess AI.
"""
import wave
import struct
import numpy as np
from pathlib import Path

AUDIO_DIR = Path(__file__).resolve().parent / "web" / "static" / "audio_samples"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def generate_sample_wav(filename: str, f0: float, f1: float, f2: float, noise_level: float = 0.15):
    sample_rate = 16000
    duration = 1.0  # seconds
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, total_samples, endpoint=False)

    # Fundamental frequency + Formant harmonics
    signal = 0.5 * np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(2 * np.pi * f1 * t) + 0.2 * np.sin(2 * np.pi * f2 * t)
    
    # Formant envelope modulation (vowel attack-decay)
    envelope = np.sin(np.pi * t / duration)
    signal = signal * envelope

    # Acoustic slurring noise
    noise = np.random.normal(0, noise_level, total_samples)
    final_signal = signal + noise
    
    # Normalize to 16-bit PCM
    final_signal = final_signal / (np.max(np.abs(final_signal)) + 1e-6)
    int_signal = (final_signal * 32767 * 0.85).astype(np.int16)

    wav_path = AUDIO_DIR / filename
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(int_signal.tobytes())

    print(f"Generated sample: {wav_path}")

if __name__ == "__main__":
    generate_sample_wav("sample_water.wav", f0=130, f1=350, f2=1200, noise_level=0.18)
    generate_sample_wav("sample_help.wav", f0=140, f1=650, f2=1850, noise_level=0.15)
    generate_sample_wav("sample_pain.wav", f0=120, f1=500, f2=1600, noise_level=0.20)
    generate_sample_wav("sample_doctor.wav", f0=110, f1=450, f2=1500, noise_level=0.16)
