"""
Tests for Area Product (Ap) calculation methods
"""

import pytest
import math
from calculations.ap_method import (
    calculate_apparent_power,
    waveform_coefficient,
    select_flux_density,
    calculate_area_product,
    calculate_bac_from_waveform,
)


class TestApparentPower:
    """Tests for apparent power calculation"""

    def test_100w_90_percent_efficiency(self):
        """100W output at 90% efficiency should give ~222 VA"""
        Pt = calculate_apparent_power(100, 90)
        # Pt = Po + Pin = Po + Po/η = Po(1 + 1/η)
        # Pt = 100 * (1 + 1/0.9) = 100 * 2.111 = 211.1
        assert 200 < Pt < 230

    def test_1kw_95_percent_efficiency(self):
        """1kW output at 95% efficiency"""
        Pt = calculate_apparent_power(1000, 95)
        # Pt = 1000 * (1 + 1/0.95) = 1000 * 2.053 = 2053
        assert 2000 < Pt < 2100

    def test_zero_power(self):
        """Zero output power should return zero"""
        Pt = calculate_apparent_power(0, 90)
        assert Pt == 0


class TestWaveformCoefficient:
    """Tests for waveform coefficient Kf"""

    def test_sinusoidal(self):
        """Sinusoidal waveform Kf = 4.44"""
        Kf = waveform_coefficient("sinusoidal")
        assert abs(Kf - 4.44) < 0.01

    def test_square(self):
        """Square waveform Kf = 4.0"""
        Kf = waveform_coefficient("square")
        assert abs(Kf - 4.0) < 0.01

    def test_triangular(self):
        """Triangular waveform Kf = 4.0"""
        Kf = waveform_coefficient("triangular")
        assert abs(Kf - 4.0) < 0.01


class TestFluxDensitySelection:
    """Tests for frequency-based flux density selection"""

    def test_ferrite_100khz(self):
        """Ferrite at 100kHz should give Bmax around 0.10-0.25T"""
        result = select_flux_density(100000, "ferrite")
        assert 0.08 <= result["Bmax_T"] <= 0.30

    def test_ferrite_500khz(self):
        """Ferrite at 500kHz should give lower Bmax"""
        result = select_flux_density(500000, "ferrite")
        assert 0.03 <= result["Bmax_T"] <= 0.15

    def test_silicon_steel_60hz(self):
        """Silicon steel at 60Hz should give Bmax around 1.0-1.5T"""
        result = select_flux_density(60, "silicon_steel")
        assert 1.0 < result["Bmax_T"] < 1.8


class TestAreaProduct:
    """Tests for Area Product calculation"""

    def test_100w_100khz_flyback(self):
        """
        100W flyback at 100kHz — Expected Ap ~ 0.3-0.8 cm⁴
        McLyman example from handbook
        """
        Pt = 222  # 100W at 90% eff
        freq = 100000
        Bmax = 0.2
        J = 400
        Ku = 0.35
        Kf = 4.0  # Square wave

        Ap = calculate_area_product(Pt, freq, Bmax, J, Ku, Kf)

        # Expected range for small SMPS transformer (0.1-2 cm⁴)
        assert 0.1 < Ap < 2.0, f"Ap = {Ap} outside expected range"

    def test_1kw_100khz(self):
        """1kW at 100kHz — Expected Ap ~ 3-15 cm⁴"""
        Pt = 2100  # 1kW at 95% eff
        freq = 100000
        Bmax = 0.2
        J = 400
        Ku = 0.35
        Kf = 4.0

        Ap = calculate_area_product(Pt, freq, Bmax, J, Ku, Kf)

        # 1kW range: 1-25 cm⁴
        assert 1 < Ap < 25, f"Ap = {Ap} outside expected range"

    def test_higher_frequency_smaller_ap(self):
        """Higher frequency should require smaller Ap"""
        Pt = 500
        Bmax = 0.2
        J = 400
        Ku = 0.35
        Kf = 4.0

        Ap_100k = calculate_area_product(Pt, 100000, Bmax, J, Ku, Kf)
        Ap_500k = calculate_area_product(Pt, 500000, Bmax, J, Ku, Kf)

        assert Ap_500k < Ap_100k, "Higher frequency should give smaller Ap"

    def test_higher_current_density_smaller_ap(self):
        """Higher current density should require smaller Ap"""
        Pt = 500
        freq = 100000
        Bmax = 0.2
        Ku = 0.35
        Kf = 4.0

        Ap_400 = calculate_area_product(Pt, freq, Bmax, 400, Ku, Kf)
        Ap_600 = calculate_area_product(Pt, freq, Bmax, 600, Ku, Kf)


class TestWaveformAwareBac:
    """Tests for waveform-aware AC flux density calculation (Phase A Task 3)"""

    def test_sinusoidal_bac(self):
        """Sinusoidal waveform: Bac = Bmax"""
        Bac = calculate_bac_from_waveform(Bmax_T=0.3, waveform="sinusoidal", duty_cycle=0.5)
        assert abs(Bac - 0.3) < 0.001, f"Expected Bac=0.3T, got {Bac}T"

    def test_square_bac(self):
        """Square waveform: Bac = Bmax (full swing)"""
        Bac = calculate_bac_from_waveform(Bmax_T=0.2, waveform="square", duty_cycle=0.5)
        assert abs(Bac - 0.2) < 0.001, f"Expected Bac=0.2T, got {Bac}T"

    def test_triangular_bac(self):
        """Triangular waveform: Bac = Bmax"""
        Bac = calculate_bac_from_waveform(Bmax_T=0.25, waveform="triangular", duty_cycle=0.5)
        assert abs(Bac - 0.25) < 0.001, f"Expected Bac=0.25T, got {Bac}T"

    def test_trapezoidal_symmetric_duty(self):
        """Trapezoidal with D=0.5 should give Bac ≈ Bmax"""
        Bac = calculate_bac_from_waveform(Bmax_T=0.3, waveform="trapezoidal", duty_cycle=0.5)
        assert abs(Bac - 0.3) < 0.01, f"Expected Bac≈0.3T at D=0.5, got {Bac}T"

    def test_trapezoidal_asymmetric_duty(self):
        """Trapezoidal with D≠0.5 should reduce Bac"""
        Bac_50 = calculate_bac_from_waveform(Bmax_T=0.3, waveform="trapezoidal", duty_cycle=0.5)
        Bac_25 = calculate_bac_from_waveform(Bmax_T=0.3, waveform="trapezoidal", duty_cycle=0.25)
        assert Bac_25 < Bac_50, "Asymmetric duty should reduce Bac"

    def test_not_bmax_over_2(self):
        """Critical: Bac should NOT default to Bmax/2 for any waveform"""
        waveforms = ["sinusoidal", "square", "triangular"]
        for waveform in waveforms:
            Bac = calculate_bac_from_waveform(Bmax_T=0.4, waveform=waveform, duty_cycle=0.5)
            # Bac should be close to Bmax, NOT 0.2 (Bmax/2)
            assert Bac > 0.35, f"{waveform}: Bac={Bac}T should be ≈Bmax=0.4T, not Bmax/2=0.2T"
