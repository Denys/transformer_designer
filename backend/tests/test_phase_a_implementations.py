"""
Unit tests for Phase A implementations
Tests geometry-derived MLT/At, layer estimation, waveform-aware Bac, and Litz wire
"""

import pytest
import math
from integrations.openmagnetics import OpenMagneticsDB


class TestGeometryDerivedMLT:
    """Tests for geometry-derived Mean Length per Turn (Phase A Task 1)"""

    def test_e_core_mlt_calculation(self):
        """E-core MLT should be calculated from geometry"""
        db = OpenMagneticsDB()
        
        # E-core with known dimensions
        MLT = db._calculate_MLT(
            shape="E",
            width_cm=3.0,
            height_cm=2.0,
            depth_cm=1.5,
            Ae_cm2=1.0,  # 1cm² center leg
        )
        
        # MLT should be reasonable for this size (roughly perimeter of center leg)
        assert 3.0 < MLT < 10.0, f"E-core MLT={MLT}cm seems unreasonable"

    def test_pq_core_mlt_calculation(self):
        """PQ/pot core MLT should be calculated from geometry"""
        db = OpenMagneticsDB()
        
        MLT = db._calculate_MLT(
            shape="PQ",
            width_cm=2.5,
            height_cm=2.5,
            depth_cm=2.5,
            Ae_cm2=0.8,
        )
        
        # PQ cores are more compact
        assert 2.0 < MLT < 8.0, f"PQ-core MLT={MLT}cm seems unreasonable"

    def test_toroid_mlt_calculation(self):
        """Toroidal core MLT calculation"""
        db = OpenMagneticsDB()
        
        MLT = db._calculate_MLT(
            shape="TOROID",
            width_cm=4.0,  # OD
            height_cm=1.0,
            depth_cm=4.0,
            Ae_cm2=1.0,
        )
        
        assert 2.0 < MLT < 12.0, f"Toroid MLT={MLT}cm seems unreasonable"

    def test_mlt_scales_with_core_size(self):
        """Larger cores should have larger MLT"""
        db = OpenMagneticsDB()
        
        MLT_small = db._calculate_MLT("E", 2.0, 1.5, 1.0, 0.5)
        MLT_large = db._calculate_MLT("E", 5.0, 4.0, 3.0, 2.0)
        
        assert MLT_large > MLT_small, "Larger core should have larger MLT"

    def test_mlt_never_zero(self):
        """MLT should never be zero or negative"""
        db = OpenMagneticsDB()
        
        MLT = db._calculate_MLT("E", 1.0, 1.0, 1.0, 0.1)
        assert MLT > 0, "MLT must be positive"

    def test_mlt_minimum_value(self):
        """MLT should have a reasonable minimum (>= 1cm)"""
        db = OpenMagneticsDB()
        
        # Even tiny cores should have MLT >= 1cm
        MLT = db._calculate_MLT("E", 0.5, 0.5, 0.5, 0.05)
        assert MLT >= 1.0, f"MLT should be at least 1cm, got {MLT}cm"


class TestGeometryDerivedSurfaceArea:
    """Tests for geometry-derived thermal surface area At (Phase A Task 1)"""

    def test_e_core_surface_area(self):
        """E-core surface area should be calculated from box dimensions"""
        db = OpenMagneticsDB()
        
        At = db._calculate_surface_area(
            shape="E",
            width_cm=3.0,
            height_cm=2.0,
            depth_cm=1.5,
            Ap_cm4=2.0,
        )
        
        # Surface area should be reasonable for this size
        # Box surface = 2*(W*H + W*D + H*D) = 2*(6 + 4.5 + 3) = 27 cm²
        # E-core exposure factor ≈ 0.6, so At ≈ 16 cm²
        assert 10.0 < At < 25.0, f"E-core At={At}cm² seems unreasonable"

    def test_pot_core_surface_area(self):
        """Pot cores have less exposed surface"""
        db = OpenMagneticsDB()
        
        At_e = db._calculate_surface_area("E", 3.0, 2.0, 1.5, 2.0)
        At_pot = db._calculate_surface_area("POT", 3.0, 2.0, 1.5, 2.0)
        
        # Pot cores are more enclosed, should have less exposed area
        assert At_pot < At_e, "Pot cores should have less exposed surface than E-cores"

    def test_toroid_surface_area(self):
        """Toroids have good all-around exposure"""
        db = OpenMagneticsDB()
        
        At = db._calculate_surface_area("TOROID", 4.0, 1.5, 4.0, 5.0)
        
        assert At > 10.0, "Toroid should have reasonable surface area"

    def test_surface_area_scales_with_size(self):
        """Larger cores should have larger surface area"""
        db = OpenMagneticsDB()
        
        At_small = db._calculate_surface_area("E", 2.0, 1.5, 1.0, 1.0)
        At_large = db._calculate_surface_area("E", 5.0, 4.0, 3.0, 8.0)
        
        assert At_large > At_small, "Larger core should have larger surface area"

    def test_surface_area_never_zero(self):
        """Surface area should never be zero or negative"""
        db = OpenMagneticsDB()
        
        At = db._calculate_surface_area("E", 1.0, 1.0, 1.0, 0.5)
        assert At > 0, "Surface area must be positive"

    def test_surface_area_minimum_value(self):
        """Surface area should have a reasonable minimum (>= 1cm²)"""
        db = OpenMagneticsDB()
        
        At = db._calculate_surface_area("E", 0.5, 0.5, 0.5, 0.1)
        assert At >= 1.0, f"Surface area should be at least 1cm², got {At}cm²"


class TestGeometryMLTAtIntegration:
    """Integration tests for MLT/At in core search"""

    def test_openmagnetics_cores_have_mlt(self):
        """Cores from OpenMagnetics should have calculated MLT"""
        db = OpenMagneticsDB()
        
        if not db.is_available:
            pytest.skip("OpenMagnetics database not available")
        
        cores = db.get_cores(min_Ap_cm4=0.5, max_Ap_cm4=2.0, limit=5)
        
        for core in cores:
            assert "MLT_cm" in core, f"Core {core['name']} missing MLT_cm"
            assert core["MLT_cm"] > 0, f"Core {core['name']} has invalid MLT={core['MLT_cm']}"

    def test_openmagnetics_cores_have_surface_area(self):
        """Cores from OpenMagnetics should have calculated At"""
        db = OpenMagneticsDB()
        
        if not db.is_available:
            pytest.skip("OpenMagnetics database not available")
        
        cores = db.get_cores(min_Ap_cm4=0.5, max_Ap_cm4=2.0, limit=5)
        
        for core in cores:
            assert "At_cm2" in core, f"Core {core['name']} missing At_cm2"
            assert core["At_cm2"] > 0, f"Core {core['name']} has invalid At={core['At_cm2']}"

    def test_no_default_mlt_constants(self):
        """MLT should be geometry-derived, not default constants"""
        db = OpenMagneticsDB()
        
        if not db.is_available:
            pytest.skip("OpenMagnetics database not available")
        
        # Get cores across a wider Ap range to ensure size variation
        cores = db.get_cores(min_Ap_cm4=0.5, max_Ap_cm4=10.0, shape_family="E", limit=20)
        
        if len(cores) >= 3:
            # Different E-cores should have different MLTs based on their size
            mlts = [c["MLT_cm"] for c in cores]
            unique_mlts = len(set(mlts))
            # Allow for some cores to have similar dimensions, but expect variation
            assert unique_mlts > 1, f"Expected MLT variation across {len(cores)} cores, got {unique_mlts} unique values"


class TestPhaseASmoke:
    """Smoke tests for Phase A - end-to-end validation"""

    def test_hf_transformer_design_100khz(self):
        """High-frequency transformer (100kHz) uses geometry-derived MLT/At and Litz"""
        # This would be tested via the API endpoint
        # For now, verify the components work together
        from calculations.ap_method import calculate_bac_from_waveform
        from calculations.winding import recommend_litz_wire, calculate_layers_from_geometry
        
        # Test waveform-aware Bac
        Bac = calculate_bac_from_waveform(0.2, "square", 0.5)
        assert 0.15 < Bac < 0.25, "Bac for square wave should be ≈Bmax"
        
        # Test Litz recommendation
        litz = recommend_litz_wire(0.01, 100000)
        assert litz.get("wire_type") == "litz", "Should recommend Litz at 100kHz"
        
        # Test layer calculation
        layers = calculate_layers_from_geometry(50, 0.5, 2.0, "E")
        assert layers["num_layers"] > 0, "Should calculate layers from geometry"

    def test_lf_transformer_design_50hz(self):
        """Low-frequency transformer (50Hz) uses solid wire, geometry-derived values"""
        from calculations.ap_method import calculate_bac_from_waveform
        from calculations.winding import select_wire_gauge, calculate_layers_from_geometry
        
        # Test waveform-aware Bac for sinusoidal
        Bac = calculate_bac_from_waveform(1.5, "sinusoidal", 0.5)
        assert 1.4 < Bac < 1.6, "Bac for sine wave should be ≈Bmax"
        
        # Test solid wire selection
        wire = select_wire_gauge(0.05, 50)
        assert wire.get("strands", 1) == 1 or "skin_effect_limited" not in wire, \
            "50Hz should not be skin-effect limited"
        
        # Test layer calculation
        layers = calculate_layers_from_geometry(200, 2.0, 5.0, "E")
        assert layers["num_layers"] > 0, "Should calculate layers from geometry"

    def test_frequency_threshold_50khz(self):
        """50kHz threshold for Litz wire recommendation"""
        from calculations.winding import recommend_litz_wire
        
        # Just below threshold
        result_49k = recommend_litz_wire(0.01, 49000)
        # Just above threshold
        result_51k = recommend_litz_wire(0.01, 51000)
        
        # At 51kHz, Litz should be recommended
        assert result_51k.get("wire_type") == "litz", "Should recommend Litz above 50kHz"