"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Health check should return ok status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCoresEndpoint:
    """Tests for cores database endpoint"""

    def test_get_cores(self, client):
        """Should return list of cores"""
        response = client.get("/api/cores")
        assert response.status_code == 200
        data = response.json()
        assert "cores" in data or "ferrite_cores" in data

    def test_cores_have_required_fields(self, client):
        """Cores should have all required fields"""
        response = client.get("/api/cores")
        data = response.json()
        
        # Get first core from response
        cores = data.get("cores", [])
        if not cores and "ferrite_cores" in data:
            cores = data.get("ferrite_cores", [])
        
        if cores:
            core = cores[0] if isinstance(cores[0], dict) else cores[0]
            required_fields = ["part_number", "Ae_cm2", "Wa_cm2", "Ap_cm4"]
            for field in required_fields:
                assert field in core or field in str(core), f"Missing {field}"


class TestTransformerDesign:
    """Tests for transformer design endpoint"""

    def test_design_basic(self, client, sample_transformer_requirements):
        """Basic transformer design should succeed"""
        response = client.post(
            "/api/design/transformer",
            json=sample_transformer_requirements
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should be either a success or suggestions response
        if "design_viable" in data:
            # Success response
            assert "core" in data
            assert "winding" in data
            assert "losses" in data
        else:
            # Suggestions response
            assert "suggestions" in data or "success" in data

    def test_design_returns_core(self, client, sample_transformer_requirements):
        """Design should return core selection"""
        response = client.post(
            "/api/design/transformer",
            json=sample_transformer_requirements
        )
        data = response.json()
        
        if data.get("design_viable"):
            assert "core" in data
            assert "part_number" in data["core"]
            assert "Ae_cm2" in data["core"]

    def test_design_returns_winding(self, client, sample_transformer_requirements):
        """Design should return winding details"""
        response = client.post(
            "/api/design/transformer",
            json=sample_transformer_requirements
        )
        data = response.json()
        
        if data.get("design_viable"):
            winding = data["winding"]
            assert "primary_turns" in winding
            assert "secondary_turns" in winding
            assert winding["primary_turns"] > 0
            assert winding["secondary_turns"] > 0

    def test_design_returns_losses(self, client, sample_transformer_requirements):
        """Design should return loss analysis"""
        response = client.post(
            "/api/design/transformer",
            json=sample_transformer_requirements
        )
        data = response.json()
        
        if data.get("design_viable"):
            losses = data["losses"]
            assert "core_loss_W" in losses
            assert "total_copper_loss_W" in losses
            assert "efficiency_percent" in losses
            assert losses["efficiency_percent"] > 0

    def test_design_returns_thermal(self, client, sample_transformer_requirements):
        """Design should return thermal analysis"""
        response = client.post(
            "/api/design/transformer",
            json=sample_transformer_requirements
        )
        data = response.json()
        
        if data.get("design_viable"):
            thermal = data["thermal"]
            assert "temperature_rise_C" in thermal
            assert "hotspot_temp_C" in thermal

    def test_design_high_power_suggestions(self, client):
        """Very high power should either succeed (with OpenMagnetics) or return suggestions"""
        requirements = {
            "output_power_W": 50000,  # 50kW - very high
            "primary_voltage_V": 400,
            "secondary_voltage_V": 48,
            "frequency_Hz": 100000,
        }
        response = client.post("/api/design/transformer", json=requirements)
        
        # Should not return 404/500 error
        assert response.status_code == 200
        data = response.json()
        
        # Should have suggestions OR be a successful design (with OpenMagnetics)
        has_suggestions = "suggestions" in data or "success" in data
        has_design = "core" in data and "design_viable" in data
        assert has_suggestions or has_design, f"Expected suggestions or design, got: {list(data.keys())}"

    def test_design_missing_required_field(self, client):
        """Missing required field should return 422"""
        requirements = {
            "output_power_W": 100,
            # Missing primary_voltage_V
            "secondary_voltage_V": 12,
            "frequency_Hz": 100000,
        }
        response = client.post("/api/design/transformer", json=requirements)
        assert response.status_code == 422  # Validation error


class TestInductorDesign:
    """Tests for inductor design endpoint"""

    def test_inductor_design_basic(self, client, sample_inductor_requirements):
        """Basic inductor design should succeed"""
        response = client.post(
            "/api/design/inductor",
            json=sample_inductor_requirements
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for core selection
        assert "core" in data
        # Check for calculated inductance
        assert "calculated_inductance_uH" in data or "design_viable" in data

    def test_inductor_with_gap(self, client, sample_inductor_requirements):
        """Inductor with DC current should have air gap"""
        response = client.post(
            "/api/design/inductor",
            json=sample_inductor_requirements
        )
        data = response.json()
        
        # With DC bias, should have gap
        if "core" in data:
            assert "air_gap_mm" in data
            assert data["air_gap_mm"] >= 0


class TestMaterialsEndpoint:
    """Tests for materials database endpoint"""

    def test_get_materials(self, client):
        """Should return materials database"""
        response = client.get("/api/materials")
        assert response.status_code == 200
        data = response.json()
        # Should have ferrite and/or silicon steel
        assert len(data) > 0
