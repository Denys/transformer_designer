
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Sample valid design result for testing
SAMPLE_DESIGN_RESULT = {
    "design_method": "kgfe_erickson",
    "design_method_name": "KgFe Erickson",
    "calculated_Ap_cm4": 1.5,
    "calculated_Kg_cm5": 0.5,
    "optimal_Pfe_Pcu_ratio": 1.0,
    "core": {
        "manufacturer": "TDK",
        "part_number": "E 42/21/20",
        "geometry": "E",
        "material": "N87",
        "Ae_cm2": 2.33,
        "Wa_cm2": 2.58,
        "Ap_cm4": 6.01,
        "MLT_cm": 9.8,
        "lm_cm": 9.7,
        "Ve_cm3": 22.6,
        "At_cm2": 91.0,
        "weight_g": 110,
    },
    "winding": {
        "primary_turns": 24,
        "primary_wire_awg": 14,
        "primary_strands": 1,
        "primary_layers": 2,
        "secondary_turns": 15,
        "secondary_wire_awg": 10,
        "secondary_strands": 1,
        "secondary_layers": 2,
    },
    "losses": {
        "core_loss_W": 2.5,
        "core_loss_density_mW_cm3": 110,
        "primary_copper_loss_W": 1.2,
        "secondary_copper_loss_W": 1.3,
        "total_copper_loss_W": 2.5,
        "total_loss_W": 5.0,
        "efficiency_percent": 98.5,
    },
    "thermal": {
        "temperature_rise_C": 35,
        "hotspot_temp_C": 60,
    },
    "magnetizing_inductance_uH": 1500,
    "leakage_inductance_uH": 5,
    "turns_ratio": 1.6,
}

SAMPLE_REQUIREMENTS = {
    "output_power_W": 500,
    "primary_voltage_V": 400,
    "secondary_voltage_V": 250,
    "frequency_Hz": 100000,
    "efficiency_percent": 98,
    "waveform": "square",
}

def test_export_formats_list():
    response = client.get("/api/export/formats")
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    formats = {f["id"]: f for f in data["formats"]}
    assert "mas" in formats
    assert "json" in formats
    assert "femm" in formats
    assert "pdf" in formats
    assert formats["pdf"]["available"] is True

def test_export_mas_download():
    response = client.post(
        "/api/export/mas/download",
        json={
            "design_result": SAMPLE_DESIGN_RESULT,
            "requirements": SAMPLE_REQUIREMENTS,
            "pretty": True,
            "include_metadata": True
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert "magnetic" in data
    assert "inputs" in data

def test_export_json_download():
    response = client.post(
        "/api/export/json/download",
        json={
            "design_result": SAMPLE_DESIGN_RESULT,
            "requirements": SAMPLE_REQUIREMENTS,
            "pretty": True,
            "include_metadata": True
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert data["type"] == "transformer_design"
    assert "design_result" in data

def test_export_pdf_download():
    response = client.post(
        "/api/export/pdf/download",
        json={
            "design_result": SAMPLE_DESIGN_RESULT,
            "requirements": SAMPLE_REQUIREMENTS,
            "pretty": True,
            "include_metadata": True
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    content = response.content
    # Check for PDF header
    assert content.startswith(b"%PDF")
