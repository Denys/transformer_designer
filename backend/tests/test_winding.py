"""
Tests for winding calculations
"""

import pytest
import math
from calculations.winding import (
    calculate_turns,
    calculate_wire_area,
    select_wire_gauge,
    calculate_dc_resistance,
    calculate_skin_depth,
    calculate_ac_resistance_factor,
    calculate_window_utilization,
)


class TestTurnsCalculation:
    """Tests for primary/secondary turns calculation using Faraday's law"""

    def test_basic_turns_calculation(self):
        """
        N = (V × 10⁴) / (Kf × Bac × f × Ae)
        100V, 100kHz, 0.2T, 1cm² Ae, Kf=4.0
        N = (100 × 10000) / (4.0 × 0.2 × 100000 × 1.0) = 1000000 / 80000 = 12.5
        """
        N = calculate_turns(
            voltage_V=100,
            frequency_Hz=100000,
            Bac_T=0.2,
            Ae_cm2=1.0,
            Kf=4.0
        )
        assert 10 < N < 15, f"Expected ~12 turns, got {N}"

    def test_higher_voltage_more_turns(self):
        """Higher voltage should require more turns"""
        N1 = calculate_turns(48, 100000, 0.2, 1.0, 4.0)
        N2 = calculate_turns(96, 100000, 0.2, 1.0, 4.0)
        assert N2 > N1, "Higher voltage should need more turns"

    def test_larger_core_fewer_turns(self):
        """Larger Ae should require fewer turns"""
        N1 = calculate_turns(48, 100000, 0.2, 1.0, 4.0)
        N2 = calculate_turns(48, 100000, 0.2, 2.0, 4.0)
        assert N2 < N1, "Larger Ae should need fewer turns"


class TestWireArea:
    """Tests for wire area calculation"""

    def test_wire_area_5a_400_density(self):
        """
        Wire area = I_rms / J
        5A at 400 A/cm² = 0.0125 cm²
        """
        area = calculate_wire_area(5.0, 400)
        # 5 / 400 = 0.0125 cm²
        assert 0.010 < area < 0.015, f"Expected ~0.0125 cm², got {area}"

    def test_higher_current_larger_wire(self):
        """Higher current should need larger wire"""
        area1 = calculate_wire_area(5.0, 400)
        area2 = calculate_wire_area(10.0, 400)
        assert area2 > area1


class TestWireGaugeSelection:
    """Tests for AWG wire gauge selection"""

    def test_select_awg_for_1mm_wire(self):
        """1mm² wire should select around AWG18"""
        result = select_wire_gauge(0.01)  # 0.01 cm² = 1 mm²
        awg = result["awg"]
        assert 16 <= awg <= 20, f"Expected AWG 17-19, got {awg}"

    def test_select_awg_for_small_wire(self):
        """Small wire (0.1 mm²) should select AWG 24-28"""
        result = select_wire_gauge(0.001)  # 0.001 cm² = 0.1 mm²
        awg = result["awg"]
        assert 24 <= awg <= 30, f"Expected AWG 24-28, got {awg}"

    def test_larger_area_smaller_awg(self):
        """Larger area should give smaller AWG number"""
        result1 = select_wire_gauge(0.01)  # 1 mm²
        result2 = select_wire_gauge(0.05)  # 5 mm²
        assert result2["awg"] < result1["awg"], "Larger wire should have smaller AWG"


class TestSkinDepth:
    """Tests for skin depth calculation"""

    def test_skin_depth_100khz_copper(self):
        """
        Skin depth at 100kHz in copper ≈ 0.21 mm
        δ = 66.1 / √f (mm) for copper at 20°C
        δ = 66.1 / √100000 = 66.1 / 316 = 0.209 mm
        """
        delta = calculate_skin_depth(100000, 100)  # 100°C
        assert 0.15 < delta < 0.35, f"Expected ~0.21mm, got {delta}"

    def test_higher_frequency_smaller_skin_depth(self):
        """Higher frequency should give smaller skin depth"""
        delta1 = calculate_skin_depth(100000, 100)
        delta2 = calculate_skin_depth(500000, 100)
        assert delta2 < delta1


class TestDcResistance:
    """Tests for DC resistance calculation"""

    def test_dc_resistance_basic(self):
        """
        R_dc = ρ × length / area
        10 turns, MLT=5cm, AWG20 (0.52mm dia) at 100°C
        """
        # AWG20: area ≈ 0.518 mm² = 0.00518 cm²
        Rdc = calculate_dc_resistance(
            turns=10,
            MLT_cm=5.0,
            wire_area_cm2=0.00518,
            temperature_C=100
        )
        # Should be a few to tens of mΩ
        assert 0 < Rdc < 0.5, f"R_dc = {Rdc} Ω seems unreasonable"

    def test_more_turns_higher_resistance(self):
        """More turns should increase resistance"""
        R1 = calculate_dc_resistance(10, 5.0, 0.005, 100)
        R2 = calculate_dc_resistance(20, 5.0, 0.005, 100)
        assert R2 > R1


class TestWindowUtilization:
    """Tests for window utilization calculation"""

    def test_window_utilization_basic(self):
        """Check Ku calculation doesn't exceed 1.0 for reasonable values"""
        result = calculate_window_utilization(
            primary_turns=20,
            primary_wire_area_cm2=0.005,
            secondary_turns=5,
            secondary_wire_area_cm2=0.02,
            window_area_cm2=1.0
        )
        Ku = result["Ku"]
        # Both windings should use some fraction of window
        assert 0 < Ku < 1.0, f"Ku = {Ku} is invalid"

    def test_overfilled_window(self):
        """Window utilization > ~0.55 should indicate overfill"""
        result = calculate_window_utilization(
            primary_turns=50,
            primary_wire_area_cm2=0.02,
            secondary_turns=50,
            secondary_wire_area_cm2=0.02,
            window_area_cm2=1.0
        )
        Ku = result["Ku"]
        # 100 turns × 0.02 cm² × 1.3 insulation = 2.6 cm² in 1 cm² = Ku > 1
        assert Ku > 0.5, "Should detect filled window"


class TestLitzWireRecommendation:
    """Tests for Litz wire recommendation (Phase A Task 4)"""

    def test_litz_not_recommended_below_10khz(self):
        """Below 10kHz, solid wire should be recommended"""
        from calculations.winding import recommend_litz_wire
        result = recommend_litz_wire(required_area_cm2=0.01, frequency_Hz=5000)
        assert result.get("wire_type") == "solid", "Should recommend solid wire below 10kHz"

    def test_litz_recommended_at_100khz(self):
        """At 100kHz, Litz wire should be effective"""
        from calculations.winding import recommend_litz_wire
        result = recommend_litz_wire(required_area_cm2=0.01, frequency_Hz=100000)
        assert result.get("wire_type") == "litz", "Should recommend Litz at 100kHz"
        assert result.get("effective_at_frequency"), "Litz should be effective at 100kHz"

    def test_litz_strand_awg_vs_frequency(self):
        """Higher frequency should recommend finer strands"""
        from calculations.winding import recommend_litz_wire
        result_50k = recommend_litz_wire(required_area_cm2=0.01, frequency_Hz=50000)
        result_500k = recommend_litz_wire(required_area_cm2=0.01, frequency_Hz=500000)
        
        if result_50k.get("wire_type") == "litz" and result_500k.get("wire_type") == "litz":
            assert result_500k["strand_awg"] >= result_50k["strand_awg"], \
                "Higher frequency should use finer strands (higher AWG)"

    def test_litz_ac_factor_near_unity(self):
        """Well-designed Litz should have AC factor close to 1.0"""
        from calculations.winding import recommend_litz_wire
        result = recommend_litz_wire(required_area_cm2=0.01, frequency_Hz=100000)
        
        if result.get("wire_type") == "litz" and result.get("effective_at_frequency"):
            ac_factor = result.get("ac_factor", 2.0)
            assert 0.9 <= ac_factor <= 1.5, \
                f"Effective Litz should have AC factor 1.0-1.5, got {ac_factor}"

    def test_litz_skin_depth_constraint(self):
        """Litz strand diameter should be ≤ 2× skin depth"""
        from calculations.winding import recommend_litz_wire, calculate_skin_depth
        freq = 200000
        result = recommend_litz_wire(required_area_cm2=0.01, frequency_Hz=freq)
        
        if result.get("wire_type") == "litz":
            skin_depth_mm = calculate_skin_depth(freq)
            strand_dia_mm = result["strand_diameter_mm"]
            assert strand_dia_mm <= 2.0 * skin_depth_mm, \
                f"Strand dia {strand_dia_mm}mm > 2×δ={2*skin_depth_mm}mm"


class TestLayerCalculationFromGeometry:
    """Tests for geometry-aware layer calculation (Phase A Task 2)"""

    def test_layer_calculation_basic(self):
        """Basic layer calculation from window geometry"""
        from calculations.winding import calculate_layers_from_geometry
        
        result = calculate_layers_from_geometry(
            num_turns=50,
            wire_diameter_mm=1.0,
            window_area_cm2=2.0,
            core_geometry="E",
        )
        
        assert result["num_layers"] > 0, "Should calculate at least 1 layer"
        assert result["turns_per_layer"] > 0, "Should calculate turns per layer"
        assert result["bobbin_width_cm"] > 0, "Should estimate bobbin width"

    def test_more_turns_more_layers(self):
        """More turns should require more layers"""
        from calculations.winding import calculate_layers_from_geometry
        
        result_20 = calculate_layers_from_geometry(
            num_turns=20, wire_diameter_mm=1.0, window_area_cm2=2.0, core_geometry="E"
        )
        result_100 = calculate_layers_from_geometry(
            num_turns=100, wire_diameter_mm=1.0, window_area_cm2=2.0, core_geometry="E"
        )
        
        assert result_100["num_layers"] > result_20["num_layers"], \
            "More turns should require more layers"

    def test_narrower_window_fewer_turns_per_layer(self):
        """Narrower window (same area) should fit fewer turns per layer"""
        from calculations.winding import calculate_layers_from_geometry
        
        # Same Wa but different aspect ratios
        result_e = calculate_layers_from_geometry(
            num_turns=50, wire_diameter_mm=1.0, window_area_cm2=2.0, core_geometry="E"  # 1.5:1
        )
        result_rm = calculate_layers_from_geometry(
            num_turns=50, wire_diameter_mm=1.0, window_area_cm2=2.0, core_geometry="RM"  # 0.8:1
        )
        
        # RM has wider window, should fit more turns per layer
        assert result_rm["turns_per_layer"] > result_e["turns_per_layer"], \
            "RM (wider window) should fit more turns per layer than E-core"

    def test_no_hardcoded_np_div_20(self):
        """Layer count should NOT be simply Np//20"""
        from calculations.winding import calculate_layers_from_geometry
        
        # Test with 60 turns - if using Np//20, would give 3 layers
        result = calculate_layers_from_geometry(
            num_turns=60, wire_diameter_mm=0.5, window_area_cm2=3.0, core_geometry="E"
        )
        
        # With small wire and large window, should NOT default to 60//20=3
        # Instead should calculate based on geometry
        layers = result["num_layers"]
        # With 0.5mm wire in 3cm² window, should fit many more turns per layer
        assert layers != 3 or result["turns_per_layer"] != 20, \
            "Should not use hardcoded Np//20 heuristic"

