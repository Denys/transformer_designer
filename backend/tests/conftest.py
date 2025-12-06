"""
Pytest configuration and fixtures for transformer designer tests
"""

import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_transformer_requirements():
    """Standard transformer design requirements for testing"""
    return {
        "output_power_W": 100,
        "primary_voltage_V": 48,
        "secondary_voltage_V": 12,
        "frequency_Hz": 100000,
        "efficiency_percent": 90,
        "regulation_percent": 5,
        "ambient_temp_C": 40,
        "max_temp_rise_C": 50,
        "cooling": "natural",
        "max_current_density_A_cm2": 400,
        "window_utilization_Ku": 0.35,
        "waveform": "square",
    }


@pytest.fixture
def sample_inductor_requirements():
    """Standard inductor design requirements for testing"""
    return {
        "inductance_uH": 100,
        "dc_current_A": 5,
        "ripple_current_A": 1,
        "frequency_Hz": 100000,
        "max_current_density_A_cm2": 400,
        "window_utilization_Ku": 0.40,
        "ambient_temp_C": 40,
        "max_temp_rise_C": 50,
    }


@pytest.fixture
def cores_data():
    """Load cores database"""
    data_path = Path(__file__).parent.parent / "data" / "cores.json"
    with open(data_path) as f:
        return json.load(f)


@pytest.fixture
def materials_data():
    """Load materials database"""
    data_path = Path(__file__).parent.parent / "data" / "materials.json"
    with open(data_path) as f:
        return json.load(f)
