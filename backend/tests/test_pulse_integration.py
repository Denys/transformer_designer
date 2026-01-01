"""
Integration tests for Pulse Transformer Design

Tests the full design flow:
1. Volt-second calculation
2. Insulation requirements
3. Pulse response analysis
4. Core selection (mocked)
5. Winding design
6. Thermal analysis
7. Verification
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app
from models.pulse_transformer import PulseTransformerRequirements, PulseApplicationType

client = TestClient(app)

# Mock data for OpenMagnetics DB
MOCK_CORES = [
    {
        "part_number": "E25/13/7-3C90",
        "manufacturer": "Ferroxcube",
        "geometry": "E",
        "material": "3C90",
        "Ae_cm2": 0.52,
        "Ap_cm4": 0.2,
        "le_cm": 5.0,
        "lm_cm": 5.0,
        "MLT_cm": 4.0,
        "Wa_cm2": 0.4,
        "weight_g": 10.0,
        "mu_i": 2000,
        "height_mm": 25.0,
        "width_mm": 25.0,
        "depth_mm": 7.0,
    },
    {
        "part_number": "E42/21/15-3C90",
        "manufacturer": "Ferroxcube",
        "geometry": "E",
        "material": "3C90",
        "Ae_cm2": 1.78,
        "Ap_cm4": 4.0,
        "le_cm": 9.7,
        "lm_cm": 9.7,
        "MLT_cm": 8.0,
        "Wa_cm2": 2.2,
        "weight_g": 50.0,
        "mu_i": 2000,
        "height_mm": 42.0,
        "width_mm": 42.0,
        "depth_mm": 15.0,
    }
]

@pytest.fixture
def mock_db():
    # Patch the function where it is imported/used.
    # Since we run with PYTHONPATH=backend, the module is 'routers.pulse_transformer'
    with patch("routers.pulse_transformer.get_openmagnetics_db") as mock_get_db:
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        # Configure find_suitable_cores to return mock cores
        mock_db_instance.find_suitable_cores.return_value = MOCK_CORES
        yield mock_db_instance

def test_full_design_flow_gate_drive(mock_db):
    """Test full design flow for a gate drive transformer."""

    requirements = {
        "application": "gate_drive",
        "primary_voltage_V": 15.0,
        "secondary_voltage_V": 15.0,
        "pulse_width_us": 5.0,
        "frequency_Hz": 100000,
        "rise_time_ns": 100,
        "duty_cycle_percent": 50.0,
        "isolation_voltage_Vrms": 1500,
        "load_resistance_ohm": 10.0,
        "load_capacitance_pF": 1000.0
    }

    response = client.post("/api/design/pulse/design", json=requirements)

    assert response.status_code == 200
    result = response.json()

    # Check key outputs
    assert result["volt_second_uVs"] == 75.0 # 15V * 5us
    assert result["turns_ratio"] == 1.0
    assert result["primary"]["turns"] > 0
    assert result["secondary"]["turns"] > 0

    # Check core selection
    assert result["core"]["Ae_cm2"] > 0
    assert result["core"]["part_number"] in [c["part_number"] for c in MOCK_CORES]

    # Check pulse response
    assert "rise_time_ns" in result["pulse_response"]
    assert result["pulse_response"]["rise_time_ns"] > 0

    # Check verification
    assert "meets_specifications" in result["verification"]

def test_full_design_flow_hv_pulse(mock_db):
    """Test full design flow for a high voltage pulse transformer (Dropless style)."""

    requirements = {
        "application": "hv_power_pulse",
        "primary_voltage_V": 800.0,
        "secondary_voltage_V": 10000.0,
        "pulse_width_us": 1000.0, # 1ms
        "frequency_Hz": 10, # Low rep rate
        "duty_cycle_percent": 1.0,
        "primary_capacitance_uF": 100.0,
        "secondary_capacitance_uF": 0.1,
        "isolation_voltage_Vrms": 5000,
        "insulation_type": "reinforced"
    }

    # Mock larger core for HV
    mock_db.find_suitable_cores.return_value = [MOCK_CORES[1]]

    response = client.post("/api/design/pulse/design", json=requirements)

    assert response.status_code == 200
    result = response.json()

    assert result["turns_ratio"] == 12.5 # 10000 / 800
    assert result["core"]["Ae_cm2"] >= 1.0 # Should select larger core

    # Check insulation
    assert result["insulation"]["impulse_withstand_kV"] >= 5.0

def test_verify_endpoint(mock_db):
    """Test the verification endpoint."""

    # First get a design
    requirements = {
        "application": "gate_drive",
        "primary_voltage_V": 15.0,
        "secondary_voltage_V": 15.0,
        "pulse_width_us": 2.0,
        "frequency_Hz": 200000,
        "isolation_voltage_Vrms": 1500,
        "load_resistance_ohm": 10.0
    }

    design_response = client.post("/api/design/pulse/design", json=requirements)
    design = design_response.json()

    # Now verify it
    verify_response = client.post("/api/design/pulse/verify", json=design)

    assert verify_response.status_code == 200
    verification = verify_response.json()

    assert "meets_specifications" in verification
    assert "margins" in verification
    assert "flux_density_percent" in verification["margins"]

def test_cores_search_endpoint(mock_db):
    """Test the core search endpoint."""

    response = client.get("/api/design/pulse/cores", params={"min_Ae_cm2": 0.1, "frequency_Hz": 100000})

    assert response.status_code == 200
    result = response.json()

    assert "cores" in result
    assert len(result["cores"]) > 0
    assert result["cores"][0]["part_number"] == MOCK_CORES[0]["part_number"]
