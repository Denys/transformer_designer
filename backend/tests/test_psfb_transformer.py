"""
Integration tests for PSFB Transformer Design
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app

client = TestClient(app)

MOCK_CORES = [
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
        "Ve_cm3": 17.3
    }
]

@pytest.fixture
def mock_db():
    # Patch get_openmagnetics_db in the psfb_transformer router
    with patch("routers.psfb_transformer.get_openmagnetics_db") as mock_get_db:
        mock_db_instance = MagicMock()
        mock_get_db.return_value = mock_db_instance
        mock_db_instance.find_suitable_cores.return_value = MOCK_CORES
        yield mock_db_instance

def test_design_psfb_transformer_basic(mock_db):
    """Test basic PSFB design flow without specific leakage target."""

    request_data = {
        "power_W": 1000.0,
        "input_voltage_V": 400.0,
        "output_voltage_V": 48.0,
        "frequency_Hz": 100000.0
    }

    response = client.post("/api/design/psfb/design", json=request_data)

    assert response.status_code == 200
    result = response.json()

    assert result["core_part_number"] == "E42/21/15-3C90"
    assert result["primary_turns"] > 0
    assert result["secondary_turns"] > 0
    assert result["core_loss_W"] > 0
    assert result["total_loss_W"] > 0
    assert result["efficiency_percent"] > 90

def test_design_psfb_transformer_target_leakage(mock_db):
    """Test PSFB design with leakage targeting."""

    # Request a specific leakage (e.g. 50uH)
    # The mock core has a min leakage around 16uH, so 50uH should require a shim gap.
    request_data = {
        "power_W": 1000.0,
        "input_voltage_V": 400.0,
        "output_voltage_V": 48.0,
        "frequency_Hz": 100000.0,
        "target_leakage_uH": 50.0
    }

    response = client.post("/api/design/psfb/design", json=request_data)

    assert response.status_code == 200
    result = response.json()

    # Check if a shim gap was calculated
    assert result["target_leakage_achieved"] is True
    assert result["leakage_inductance_uH"] > 20.0

    # Check that it's close to target
    assert abs(result["leakage_inductance_uH"] - 50.0) < 1.0
    assert result["required_shim_gap_mm"] > 0

def test_design_psfb_transformer_impossible_leakage(mock_db):
    """Test impossible leakage target (too low)."""

    # Request very low leakage (e.g. 1uH) which is below the physical minimum for this core/turns
    request_data = {
        "power_W": 1000.0,
        "input_voltage_V": 400.0,
        "output_voltage_V": 48.0,
        "frequency_Hz": 100000.0,
        "target_leakage_uH": 1.0
    }

    response = client.post("/api/design/psfb/design", json=request_data)

    assert response.status_code == 200
    result = response.json()

    assert result["target_leakage_achieved"] is False
    assert len(result["warnings"]) > 0
