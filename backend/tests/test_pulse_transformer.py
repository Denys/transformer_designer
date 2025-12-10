"""
Tests for pulse transformer API endpoints

Tests both gate-drive and HV power pulse (Dropless-style) applications
"""

import pytest
from fastapi.testclient import TestClient


class TestPulseTransformerDesign:
    """Tests for pulse transformer design endpoint"""

    def test_design_gate_drive_basic(self, client):
        """Basic gate drive pulse transformer design should succeed"""
        requirements = {
            "application": "gate_drive",
            "primary_voltage_V": 15,
            "secondary_voltage_V": 15,
            "pulse_width_us": 10,
            "duty_cycle_percent": 50,
            "frequency_Hz": 100000,
            "isolation_voltage_Vrms": 2500,
            "insulation_type": "basic",
            "overvoltage_category": "II",
            "pollution_degree": 2,
        }
        response = client.post("/api/design/pulse/design", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        assert "core" in data
        assert "primary" in data
        assert "secondary" in data
        assert "pulse_response" in data
        assert "insulation" in data

    @pytest.mark.skip(reason="OpenMagnetics has no silicon-steel cores large enough for kV/kA pulse")
    def test_design_hv_power_pulse(self, client):
        """HV power pulse design (Dropless-style) - requires custom core database"""
        requirements = {
            "application": "hv_power_pulse",
            "primary_voltage_V": 200,
            "secondary_voltage_V": 3500,
            "pulse_width_us": 2500,
            "duty_cycle_percent": 31.25,
            "frequency_Hz": 125,
            "peak_current_A": 1750,
            "isolation_voltage_Vrms": 4000,
            "insulation_type": "reinforced",
            "overvoltage_category": "II",
            "pollution_degree": 2,
            "core_material_type": "silicon_steel",
            "primary_turns": 2,
            "secondary_turns": 50,
        }
        response = client.post("/api/design/pulse/design", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        assert "core" in data
        assert "primary" in data
        assert data["primary"]["turns"] == 2

    def test_returns_wire_type(self, client):
        """Design should return wire type for gate drive applications"""
        requirements = {
            "application": "gate_drive",
            "primary_voltage_V": 15,
            "secondary_voltage_V": 15,
            "pulse_width_us": 10,
            "duty_cycle_percent": 50,
            "frequency_Hz": 100000,
            "isolation_voltage_Vrms": 1500,
            "insulation_type": "basic",
            "overvoltage_category": "II",
            "pollution_degree": 2,
        }
        response = client.post("/api/design/pulse/design", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        assert "primary" in data
        assert data["primary"]["wire_type"] in ["solid", "cable", "foil"]

    def test_returns_pulse_response(self, client):
        """Design should return pulse response analysis"""
        requirements = {
            "application": "gate_drive",
            "primary_voltage_V": 15,
            "secondary_voltage_V": 15,
            "pulse_width_us": 10,
            "duty_cycle_percent": 50,
            "frequency_Hz": 100000,
            "isolation_voltage_Vrms": 1500,
            "insulation_type": "basic",
            "overvoltage_category": "II",
            "pollution_degree": 2,
        }
        response = client.post("/api/design/pulse/design", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        pr = data["pulse_response"]
        assert "rise_time_ns" in pr
        assert "droop_percent" in pr
        assert "backswing_percent" in pr
        assert "bandwidth_3dB_MHz" in pr

    def test_returns_insulation_requirements(self, client):
        """Design should return IEC 60664 insulation requirements"""
        requirements = {
            "application": "gate_drive",
            "primary_voltage_V": 15,
            "secondary_voltage_V": 15,
            "pulse_width_us": 10,
            "duty_cycle_percent": 50,
            "frequency_Hz": 100000,
            "isolation_voltage_Vrms": 4000,
            "insulation_type": "reinforced",
            "overvoltage_category": "III",
            "pollution_degree": 2,
        }
        response = client.post("/api/design/pulse/design", json=requirements)
        assert response.status_code == 200
        data = response.json()
        
        ins = data["insulation"]
        assert "clearance_mm" in ins
        assert "creepage_mm" in ins
        assert "solid_insulation_mm" in ins
        assert ins["clearance_mm"] > 0


class TestPulsePresets:
    """Tests for gate driver presets"""

    def test_get_presets(self, client):
        """Should return gate driver presets"""
        response = client.get("/api/design/pulse/presets")
        assert response.status_code == 200
        data = response.json()
        
        assert "presets" in data
        presets = data["presets"]
        
        assert "mosfet_100v" in presets or len(presets) > 0


class TestVoltSecondCalculator:
    """Tests for volt-second calculation"""

    def test_volt_second_basic(self, client):
        """Basic volt-second calculation should work"""
        # Note: This endpoint uses POST with query params (not JSON body)
        response = client.post(
            "/api/design/pulse/volt-second",
            params={
                "voltage_V": 15,
                "pulse_width_us": 10,
                "duty_cycle_percent": 50,
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "volt_second_uVs" in data
        # V*t = 15V * 10us = 150 V·µs
        assert data["volt_second_uVs"] == 150


class TestApplicationTypes:
    """Tests for application types endpoint"""

    def test_get_application_types(self, client):
        """Should return list of application types"""
        response = client.get("/api/design/pulse/applications")
        assert response.status_code == 200
        data = response.json()
        
        assert "applications" in data
        app_ids = [a["id"] for a in data["applications"]]
        
        # Check for HV power pulse support
        assert "hv_power_pulse" in app_ids or "hv_pulse" in app_ids

