"""
Integration tests for Export Functionality
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app

client = TestClient(app)

# Sample design result for testing
SAMPLE_DESIGN = {
    "application": "power_transformer",
    "core": {
        "part_number": "E25/13/7-3C90",
        "manufacturer": "Ferroxcube",
        "material": "3C90",
        "geometry": "E",
        "Ae_cm2": 0.52,
        "Ap_cm4": 0.2,
        "Wa_cm2": 0.4
    },
    "primary": {
        "turns": 100,
        "wire_type": "solid",
        "wire_awg": 24,
        "layers": 2,
        "Rdc_mOhm": 500,
        "wire_diameter_mm": 0.5
    },
    "secondary": {
        "turns": 10,
        "wire_type": "solid",
        "wire_awg": 18,
        "layers": 1,
        "Rdc_mOhm": 50,
        "wire_diameter_mm": 1.0
    },
    "core_loss_W": 0.5,
    "copper_loss_W": 0.5,
    "total_loss_W": 1.0,
    "efficiency_percent": 95.0,
    "temp_rise_C": 30.0,
    "verification": {
        "meets_specifications": True,
        "warnings": []
    }
}

SAMPLE_REQUIREMENTS = {
    "output_power_W": 20.0,
    "input_voltage_V": 230.0,
    "output_voltage_V": 12.0
}

def test_pdf_export_endpoint():
    """Test PDF export endpoint returns a PDF file."""

    request_data = {
        "design_result": SAMPLE_DESIGN,
        "requirements": SAMPLE_REQUIREMENTS,
        "pretty": True,
        "include_metadata": True
    }

    response = client.post("/api/export/pdf/download", json=request_data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert b"%PDF" in response.content # Check PDF header magic bytes

def test_svg_export_endpoint():
    """Test SVG export endpoint returns an SVG file."""

    request_data = {
        "design_result": SAMPLE_DESIGN,
        "requirements": SAMPLE_REQUIREMENTS
    }

    response = client.post("/api/export/svg/download", json=request_data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in response.content
    assert b"Primary" in response.content # Check for labels
