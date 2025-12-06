"""
Tests for thermal analysis calculations
"""

import pytest
from calculations.thermal import (
    calculate_surface_area,
    calculate_temperature_rise,
    calculate_power_dissipation_density,
    thermal_analysis,
)


class TestSurfaceArea:
    """Tests for core surface area estimation"""

    def test_surface_area_basic(self):
        """Surface area should be positive and reasonable"""
        At = calculate_surface_area(Ap_cm4=1.0, core_type="EE")
        # For 1 cm⁴ core, At = Ks × sqrt(Ap) = 39 × 1 = 39 cm²
        assert 30 < At < 50, f"At = {At} cm² seems wrong"

    def test_larger_ap_larger_area(self):
        """Larger Ap should give larger surface area"""
        At1 = calculate_surface_area(Ap_cm4=1.0, core_type="EE")
        At2 = calculate_surface_area(Ap_cm4=10.0, core_type="EE")
        assert At2 > At1


class TestTemperatureRise:
    """Tests for temperature rise calculation"""

    def test_temperature_rise_basic(self):
        """
        ΔT ≈ 450 × ψ^0.826
        At ψ = 0.05 W/cm²: ΔT ≈ 450 × 0.05^0.826 ≈ 35°C
        """
        psi = 0.05
        dT = calculate_temperature_rise(psi, "natural")
        assert 20 < dT < 60, f"ΔT = {dT}°C seems unreasonable"

    def test_forced_cooling_lower_rise(self):
        """Forced cooling should reduce temperature rise"""
        psi = 0.1
        dT_natural = calculate_temperature_rise(psi, "natural")
        dT_forced = calculate_temperature_rise(psi, "forced")
        assert dT_forced < dT_natural, "Forced cooling should reduce ΔT"


class TestThermalAnalysis:
    """Tests for complete thermal analysis"""

    def test_thermal_analysis_pass(self):
        """Low loss should pass thermal check"""
        result = thermal_analysis(
            total_loss_W=1.0,
            surface_area_cm2=50,
            ambient_temp_C=40,
            max_temp_rise_C=50,
            cooling="natural"
        )
        assert result["status"] in ["ok", "pass", "warning"]
        assert result["temperature_rise_C"] < 50

    def test_thermal_analysis_high_loss(self):
        """Very high loss should fail or warn thermal check"""
        result = thermal_analysis(
            total_loss_W=50.0,  # Very high for small surface
            surface_area_cm2=20,
            ambient_temp_C=40,
            max_temp_rise_C=40,
            cooling="natural"
        )
        # Should either fail or give warning
        assert result["status"] in ["warning", "error", "fail"]

    def test_thermal_analysis_hotspot(self):
        """Hotspot temperature should be ambient + rise"""
        result = thermal_analysis(
            total_loss_W=2.0,
            surface_area_cm2=50,
            ambient_temp_C=40,
            max_temp_rise_C=50,
            cooling="natural"
        )
        expected_min = 40 + 5  # At least ambient + some rise
        assert result["hotspot_temp_C"] > expected_min
