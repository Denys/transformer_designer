"""
Tests for loss calculations (core and copper losses)
"""

import pytest
import math
from calculations.losses import (
    calculate_core_loss_steinmetz,
    calculate_copper_loss,
    calculate_total_losses,
    calculate_efficiency,
)


class TestCoreLossSteinmetz:
    """Tests for Steinmetz equation core loss calculation"""

    def test_steinmetz_basic(self):
        """
        Pfe = k × f^α × B^β × Ve
        Typical ferrite N87: k ≈ 1.1e-3, α ≈ 1.3, β ≈ 2.5
        At 100kHz, 0.1T, 10cm³
        """
        result = calculate_core_loss_steinmetz(
            volume_cm3=10,
            frequency_Hz=100000,
            Bac_T=0.1,
            material="ferrite",
            temperature_C=100
        )
        # Should return tuple (core_loss_W, loss_density_mW_cm3)
        Pfe = result[0] if isinstance(result, tuple) else result
        # Core loss can vary widely - just check it's positive and reasonable
        assert 0 <= Pfe < 50, f"Core loss {Pfe}W seems unreasonable"

    def test_higher_flux_higher_loss(self):
        """Higher flux density should increase core loss"""
        P1 = calculate_core_loss_steinmetz(10, 100000, 0.1, "ferrite")[0]
        P2 = calculate_core_loss_steinmetz(10, 100000, 0.2, "ferrite")[0]
        assert P2 > P1, "Higher Bac should give higher core loss"

    def test_higher_frequency_higher_loss(self):
        """Higher frequency should increase core loss"""
        P1 = calculate_core_loss_steinmetz(10, 100000, 0.1, "ferrite")[0]
        P2 = calculate_core_loss_steinmetz(10, 200000, 0.1, "ferrite")[0]
        assert P2 > P1, "Higher frequency should give higher core loss"

    def test_larger_core_higher_loss(self):
        """Larger core volume should increase total core loss"""
        P1 = calculate_core_loss_steinmetz(10, 100000, 0.1, "ferrite")[0]
        P2 = calculate_core_loss_steinmetz(20, 100000, 0.1, "ferrite")[0]
        assert P2 > P1, "Larger volume should give higher core loss"


class TestCopperLoss:
    """Tests for copper (winding) loss calculation"""

    def test_copper_loss_basic(self):
        """
        Pcu = I² × R
        5A through 10mΩ = 0.25W
        """
        Pcu = calculate_copper_loss(
            Rdc_ohm=0.010,
            current_rms_A=5.0,
            Rac_Rdc_ratio=1.5
        )
        # With Rac/Rdc = 1.5: Pcu = 5² × 0.01 × 1.5 = 0.375W (approx with temp)
        assert 0.2 < Pcu < 0.8, f"Pcu = {Pcu}W unexpected"

    def test_higher_current_higher_loss(self):
        """Higher current should quadratically increase loss"""
        P1 = calculate_copper_loss(0.01, 5.0, 1.0)
        P2 = calculate_copper_loss(0.01, 10.0, 1.0)
        # P2 should be ~4× P1 (I² relationship)
        assert 3.0 < (P2 / P1) < 5.0, "Loss should scale as I²"

    def test_higher_resistance_higher_loss(self):
        """Higher resistance should linearly increase loss"""
        P1 = calculate_copper_loss(0.01, 5.0, 1.0)
        P2 = calculate_copper_loss(0.02, 5.0, 1.0)
        assert 1.5 < (P2 / P1) < 2.5, "Loss should scale approximately with R"


class TestTotalLosses:
    """Tests for total loss calculation"""

    def test_total_losses_sum(self):
        """Total losses should be sum of core and copper"""
        Pfe = 1.0  # 1W core loss
        Pcu_pri = 0.5  # 0.5W primary copper
        Pcu_sec = 0.5  # 0.5W secondary copper

        result = calculate_total_losses(Pfe, Pcu_pri, Pcu_sec)
        total = result["total_loss_W"]
        assert abs(total - 2.0) < 0.01, f"Expected 2W, got {total}"


class TestEfficiency:
    """Tests for efficiency calculation"""

    def test_efficiency_basic(self):
        """
        η = Pout / (Pout + Ploss)
        100W output, 10W loss → η = 100/110 = 90.9%
        """
        eta = calculate_efficiency(100, 10)
        assert 90 < eta < 92, f"Expected ~90.9%, got {eta}"

    def test_efficiency_no_loss(self):
        """Zero loss should give 100% efficiency"""
        eta = calculate_efficiency(100, 0)
        assert abs(eta - 100) < 0.01

    def test_high_loss_low_efficiency(self):
        """High loss should give low efficiency"""
        eta = calculate_efficiency(100, 100)  # 50% efficiency
        assert 49 < eta < 51
