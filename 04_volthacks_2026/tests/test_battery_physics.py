"""
Unit tests for Battery Electrochemistry, Thevenin ECM, Randles EIS, and SEI Growth.
"""

import pytest
import math
from voltpulse.core.battery_physics import (
    TheveninECM,
    RandlesEISModel,
    calculate_sei_growth,
)


def test_thevenin_ecm_polarization():
    ecm = TheveninECM(r0_mohm=1.2, r1_mohm=0.8, c1_farads=1500.0)
    # Step with 50A load for 2 seconds
    v_drop, v_rc = ecm.step(i_load_a=50.0, dt=2.0)

    # Ohmic drop: 50 * 0.0012 = 0.06V
    assert v_drop >= 0.06
    assert v_rc > 0.0


def test_randles_eis_nyquist_spectrum():
    eis = RandlesEISModel(r_s_mohm=0.85, r_ct_mohm=1.45)
    spectrum = eis.compute_nyquist_spectrum(soh_pct=95.0, temp_c=25.0, num_points=30)

    assert len(spectrum) == 30
    # Highest frequency point should have Z_real close to R_s
    assert spectrum[0].frequency_hz >= 1000.0
    assert 0.5 < spectrum[0].z_real_mohm < 2.5
    # All Z_imag values should be valid
    for pt in spectrum:
        assert pt.magnitude_mohm > 0.0


def test_sei_growth_physics():
    fresh_sei = calculate_sei_growth(cycles=10, avg_temp_c=25.0)
    aged_sei = calculate_sei_growth(cycles=600, avg_temp_c=35.0)

    assert fresh_sei["soh_pct"] > aged_sei["soh_pct"]
    assert aged_sei["capacity_loss_pct"] > fresh_sei["capacity_loss_pct"]
    assert aged_sei["sei_thickness_nm"] > fresh_sei["sei_thickness_nm"]
    assert aged_sei["resistance_increase_pct"] > fresh_sei["resistance_increase_pct"]
