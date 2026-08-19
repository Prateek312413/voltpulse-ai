"""
Electrochemical & Physics-Informed Battery Degradation Models (Thevenin ECM, Randles EIS, SEI Growth).
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel


class EISDataPoint(BaseModel):
    frequency_hz: float
    z_real_mohm: float
    z_imag_neg_mohm: float  # -Z_imag for standard Nyquist plot
    phase_deg: float
    magnitude_mohm: float


class TheveninECM:
    """
    1st-Order Thevenin Equivalent Circuit Model (ECM).
    Captures fast Ohmic IR drop and slower charge transfer polarization relaxation.
    """

    def __init__(self, r0_mohm: float = 1.2, r1_mohm: float = 0.8, c1_farads: float = 1500.0):
        self.r0 = r0_mohm * 1e-3  # Ohms
        self.r1 = r1_mohm * 1e-3  # Ohms
        self.c1 = c1_farads       # Farads
        self.v_rc = 0.0           # Polarization capacitor voltage

    def step(self, i_load_a: float, dt: float) -> Tuple[float, float]:
        """
        Update polarization voltage and return (V_drop_total, V_rc).
        dV_rc / dt = -V_rc / (R1 * C1) + I / C1
        """
        tau = self.r1 * self.c1
        # Analytical discrete solution: V_rc(t+dt) = V_rc * exp(-dt/tau) + I * R1 * (1 - exp(-dt/tau))
        decay = math.exp(-dt / max(1e-4, tau))
        self.v_rc = self.v_rc * decay + i_load_a * self.r1 * (1.0 - decay)

        v_ohmic = i_load_a * self.r0
        v_total_drop = v_ohmic + self.v_rc
        return v_total_drop, self.v_rc


class RandlesEISModel:
    """
    Electrochemical Impedance Spectroscopy (EIS) Randles Circuit with Constant Phase Element (CPE).
    Simulates high, mid, and low frequency electrochemistry:
    Z(w) = Rs + Rct / (1 + (j*w*Rct*Cdl)^alpha) + Zw(w)
    """

    def __init__(
        self,
        r_s_mohm: float = 0.85,
        r_ct_mohm: float = 1.45,
        c_dl_farads: float = 0.08,
        alpha_cpe: float = 0.88,
        sigma_warburg: float = 0.45
    ):
        self.r_s = r_s_mohm
        self.r_ct = r_ct_mohm
        self.c_dl = c_dl_farads
        self.alpha = alpha_cpe
        self.sigma_w = sigma_warburg

    def compute_nyquist_spectrum(
        self,
        soh_pct: float = 100.0,
        temp_c: float = 25.0,
        num_points: int = 50
    ) -> List[EISDataPoint]:
        """
        Generate full Nyquist EIS spectrum from 10 kHz down to 10 mHz.
        Adjusts R_s and R_ct dynamically based on temperature and SOH aging.
        """
        # SOH aging increases R_s and R_ct
        aging_factor = 1.0 + (100.0 - soh_pct) * 0.025
        # Arrhenius temperature scaling: higher temp reduces internal resistance
        t_kelvin = temp_c + 273.15
        temp_factor = math.exp((2500.0 / 298.15) - (2500.0 / t_kelvin))

        r_s_eff = self.r_s * aging_factor * temp_factor
        r_ct_eff = self.r_ct * (aging_factor ** 1.3) * temp_factor
        sigma_eff = self.sigma_w * aging_factor

        # Frequencies from 10,000 Hz down to 0.01 Hz on log scale
        freqs = np.logspace(4, -2, num_points)
        spectrum: List[EISDataPoint] = []

        for f in freqs:
            w = 2.0 * math.pi * f

            # 1. Ohmic resistance
            z_ohmic = complex(r_s_eff, 0.0)

            # 2. Charge transfer + CPE: Z_cpe = 1 / (Q * (j*w)^alpha)
            # Z_parallel = Rct / (1 + Rct * Q * (j*w)^alpha)
            j_w_alpha = (1j * w) ** self.alpha
            cpe_admittance = self.c_dl * j_w_alpha
            z_arc = r_ct_eff / (1.0 + r_ct_eff * cpe_admittance)

            # 3. Warburg diffusion tail (low frequency 45-degree slope)
            # Zw = sigma / sqrt(w) * (1 - 1j)
            sqrt_w = math.sqrt(max(1e-6, w))
            z_warburg = complex(sigma_eff / sqrt_w, -sigma_eff / sqrt_w)

            z_total = z_ohmic + z_arc + z_warburg

            z_real = z_total.real
            z_imag_neg = -z_total.imag
            magnitude = math.sqrt(z_real ** 2 + z_imag_neg ** 2)
            phase = math.degrees(math.atan2(z_total.imag, z_real))

            spectrum.append(EISDataPoint(
                frequency_hz=round(float(f), 4),
                z_real_mohm=round(float(z_real), 4),
                z_imag_neg_mohm=round(float(z_imag_neg), 4),
                phase_deg=round(float(phase), 2),
                magnitude_mohm=round(float(magnitude), 4)
            ))

        return spectrum


def calculate_sei_growth(
    cycles: int,
    avg_temp_c: float = 30.0,
    c_rate: float = 1.0,
    dod_pct: float = 80.0
) -> Dict[str, float]:
    """
    Physics-informed Solid Electrolyte Interphase (SEI) growth & capacity fade equation.
    Q_loss = k_arrhenius * sqrt(cycles) * (DoD / 100)^1.2 * (C_rate)^0.6
    """
    t_k = avg_temp_c + 273.15
    e_a = 31500.0  # Activation energy J/mol
    r_const = 8.314
    k_arrhenius = 0.022 * math.exp(-e_a / (r_const * t_k)) * 1e5

    dod_factor = math.pow(max(0.1, dod_pct / 100.0), 1.2)
    c_rate_factor = math.pow(max(0.1, c_rate), 0.6)

    capacity_loss_pct = k_arrhenius * math.sqrt(max(1, cycles)) * dod_factor * c_rate_factor
    capacity_loss_pct = min(40.0, max(0.0, capacity_loss_pct))
    soh_pct = max(60.0, round(100.0 - capacity_loss_pct, 2))

    # Internal resistance growth
    resistance_increase_pct = round(capacity_loss_pct * 1.85, 2)

    return {
        "soh_pct": soh_pct,
        "capacity_loss_pct": round(capacity_loss_pct, 2),
        "sei_thickness_nm": round(15.0 + capacity_loss_pct * 2.8, 1),
        "resistance_increase_pct": resistance_increase_pct
    }
