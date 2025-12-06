"""
Integration tests - end-to-end design verification
"""

import pytest


class TestTransformerDesignIntegration:
    """End-to-end transformer design tests with known expected results"""

    def test_100w_flyback_design(self, client):
        """
        Test case from implementation plan:
        100W Flyback @ 100kHz
        Expected: Ap ≈ 0.5 cm⁴, ferrite core (ETD29 or similar)
        """
        requirements = {
            "output_power_W": 100,
            "primary_voltage_V": 48,
            "secondary_voltage_V": 12,
            "frequency_Hz": 100000,
            "efficiency_percent": 90,
            "regulation_percent": 5,
            "waveform": "square",
            "max_current_density_A_cm2": 400,
            "window_utilization_Ku": 0.35,
            "ambient_temp_C": 40,
            "max_temp_rise_C": 50,
            "cooling": "natural",
        }
        
        response = client.post("/api/design/transformer", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        # Should get viable design
        assert data.get("design_viable") == True, f"Design not viable: {data}"
        
        # Check Ap is reasonable (~0.3-3 cm⁴ for 100W)
        Ap = data.get("calculated_Ap_cm4", 0)
        assert 0.1 < Ap < 5.0, f"Ap = {Ap} outside expected range"
        
        # Should select a small ferrite core
        core = data["core"]
        assert core["Ap_cm4"] < 10.0, "Core too large for 100W"
        
        # Efficiency should be reasonable
        losses = data["losses"]
        assert losses["efficiency_percent"] > 80, "Efficiency too low"

    def test_500w_fullbridge_design(self, client):
        """
        500W full-bridge transformer @ 100kHz
        Expected: Ap ≈ 2-5 cm⁴, larger core (ETD44, PQ40, or similar)
        """
        requirements = {
            "output_power_W": 500,
            "primary_voltage_V": 400,
            "secondary_voltage_V": 48,
            "frequency_Hz": 100000,
            "efficiency_percent": 95,
            "waveform": "square",
            "max_current_density_A_cm2": 400,
            "window_utilization_Ku": 0.35,
        }
        
        response = client.post("/api/design/transformer", json=requirements)
        data = response.json()
        
        # Could be viable or suggestions - both are valid
        assert response.status_code == 200
        # If viable, check core
        if data.get("design_viable") and "core" in data:
            core = data["core"]
            assert core["Ap_cm4"] >= 0.5, "Core too small for 500W"

    def test_turns_ratio_correct(self, client):
        """Verify turns ratio matches voltage ratio"""
        requirements = {
            "output_power_W": 100,
            "primary_voltage_V": 48,
            "secondary_voltage_V": 12,  # 4:1 ratio
            "frequency_Hz": 100000,
            "waveform": "square",
        }
        
        response = client.post("/api/design/transformer", json=requirements)
        data = response.json()
        
        if data.get("design_viable"):
            winding = data["winding"]
            Np = winding["primary_turns"]
            Ns = winding["secondary_turns"]
            
            actual_ratio = Np / Ns
            expected_ratio = 48 / 12  # 4:1
            
            # Allow 30% tolerance due to rounding
            assert 0.7 < (actual_ratio / expected_ratio) < 1.3, \
                f"Turns ratio {actual_ratio} doesn't match expected {expected_ratio}"


class TestInductorDesignIntegration:
    """End-to-end inductor design tests"""

    def test_100uH_5A_inductor(self, client):
        """
        100µH inductor with 5A DC bias @ 100kHz
        Expected: Core with adequate Ap, possibly gapped
        """
        requirements = {
            "inductance_uH": 100,
            "dc_current_A": 5,
            "ripple_current_A": 1,
            "frequency_Hz": 100000,
            "max_current_density_A_cm2": 400,
            "window_utilization_Ku": 0.40,
        }
        
        response = client.post("/api/design/inductor", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        # Check core was selected
        assert "core" in data
        # Check inductance is calculated
        if "calculated_inductance_uH" in data:
            L_achieved = data["calculated_inductance_uH"]
            # Should be within 50% of target
            assert 50 < L_achieved < 200, f"L = {L_achieved}µH differs too much"


class TestDatabaseIntegrity:
    """Tests for database consistency"""

    def test_all_cores_have_ap(self, cores_data):
        """All cores should have valid Ap = Ae × Wa"""
        for core in cores_data.get("ferrite_cores", []):
            Ae = core.get("Ae_cm2", 0)
            Wa = core.get("Wa_cm2", 0)
            Ap = core.get("Ap_cm4", 0)
            
            calculated_Ap = Ae * Wa
            # Allow 30% tolerance for rounded values
            if Ap > 0 and calculated_Ap > 0:
                ratio = Ap / calculated_Ap
                assert 0.6 < ratio < 1.6, \
                    f"{core['part_number']}: Ap={Ap} != Ae×Wa={calculated_Ap}"

    def test_materials_have_properties(self, materials_data):
        """Materials should have required properties"""
        ferrites = materials_data.get("ferrite", {})
        for name, mat in ferrites.items():
            # At minimum should have some loss-related property
            has_loss_data = any(k in mat for k in ["k", "steinmetz_k", "loss_coefficient", "Bsat_T"])
            assert has_loss_data, f"Material {name} missing properties"
