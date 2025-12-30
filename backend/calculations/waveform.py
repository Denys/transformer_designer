"""
Waveform analysis for transformer design

Handles:
- Non-sinusoidal waveform analysis
- RMS and effective frequency calculations
- Volt-second product calculations for various shapes
"""

import math
from enum import Enum
from typing import Optional, Union, Tuple
import numpy as np

from models.waveform import WaveformType, PulseWaveform


def calculate_volt_seconds(waveform: PulseWaveform) -> float:
    """
    Calculate V·s for any waveform type.

    Args:
        waveform: PulseWaveform object

    Returns:
        Volt-second product [V·s]
    """
    if waveform.waveform_type == WaveformType.SQUARE:
        # Simple rectangular area
        return waveform.peak_voltage * waveform.pulse_width

    elif waveform.waveform_type == WaveformType.TRIANGULAR:
        # Triangle area
        return 0.5 * waveform.peak_voltage * waveform.pulse_width

    elif waveform.waveform_type == WaveformType.SINUSOIDAL:
        # Half-sine pulse (0 to π)
        # Average value of sine over half cycle is 2/π * Vpk
        # Area = Average * time = (2/π * Vpk) * t_pulse
        return (2 / math.pi) * waveform.peak_voltage * waveform.pulse_width

    elif waveform.waveform_type == WaveformType.CAPACITOR_DISCHARGE:
        # Exponential decay: V(t) = V0 * exp(-t/RC)
        # However, for pulse transformer, we often have a clamped pulse or limited duration
        # If pulse_width is the full discharge time (approximated):
        # Integral V(t)dt from 0 to T
        if waveform.source_capacitance and waveform.circuit_resistance:
            tau = waveform.source_capacitance * waveform.circuit_resistance
            # Integral of V0*exp(-t/tau) from 0 to t_pulse is V0*tau*(1-exp(-t_pulse/tau))
            return waveform.peak_voltage * tau * (1 - math.exp(-waveform.pulse_width / tau))
        else:
            # Fallback to square approximation if R, C not known (conservative)
            return waveform.peak_voltage * waveform.pulse_width

    else:
        # Default to square (conservative)
        return waveform.peak_voltage * waveform.pulse_width


def calculate_rms_voltage(waveform: PulseWaveform) -> float:
    """
    Calculate RMS voltage for loss calculations.

    Args:
        waveform: PulseWaveform object

    Returns:
        RMS voltage [V]
    """
    # Duty cycle
    D = waveform.pulse_width * waveform.repetition_rate

    if waveform.waveform_type == WaveformType.SQUARE:
        # Vrms = Vpk * sqrt(D)
        return waveform.peak_voltage * math.sqrt(D)

    elif waveform.waveform_type == WaveformType.TRIANGULAR:
        # Vrms = Vpk * sqrt(D/3)
        return waveform.peak_voltage * math.sqrt(D / 3)

    elif waveform.waveform_type == WaveformType.SINUSOIDAL:
        # For continuous sine: Vpk/sqrt(2)
        # For pulsed sine (half-wave pulses):
        # Energy per pulse = integral(V^2 dt) = integral(Vpk^2 sin^2(wt) dt)
        # Over half period T/2, integral sin^2 = T/4
        # So integral V^2 = Vpk^2 * T/4
        # Avg power = (Vpk^2 * T/4) * f_rep
        # Vrms = sqrt(Avg Power) = Vpk * sqrt(T * f_rep / 4)
        # Since T/2 = t_pulse -> T = 2*t_pulse
        # Vrms = Vpk * sqrt(2*t_pulse * f_rep / 4) = Vpk * sqrt(D/2)
        return waveform.peak_voltage * math.sqrt(D / 2)

    elif waveform.waveform_type == WaveformType.CAPACITOR_DISCHARGE:
        # Exponential decay
        if waveform.source_capacitance and waveform.circuit_resistance:
            tau = waveform.source_capacitance * waveform.circuit_resistance
            # Integral V^2 dt = Integral V0^2 exp(-2t/tau) dt
            # = V0^2 * (-tau/2) * [exp(-2t/tau)] from 0 to t_pulse
            # = V0^2 * (tau/2) * (1 - exp(-2t_pulse/tau))
            energy_factor = (tau / 2) * (1 - math.exp(-2 * waveform.pulse_width / tau))
            return waveform.peak_voltage * math.sqrt(energy_factor * waveform.repetition_rate)
        else:
            # Fallback to square
            return waveform.peak_voltage * math.sqrt(D)

    return waveform.peak_voltage * math.sqrt(D)


def calculate_effective_frequency(waveform: PulseWaveform) -> float:
    """
    Calculate effective frequency for skin effect.

    For pulses, high frequency content is determined by rise time.
    f_eff ≈ 0.35 / t_rise

    Args:
        waveform: PulseWaveform object

    Returns:
        Effective frequency [Hz]
    """
    if waveform.rise_time > 0:
        return 0.35 / waveform.rise_time

    # If no rise time specified, estimate from pulse width
    # Assume rise time is ~5% of pulse width for "square"
    if waveform.waveform_type == WaveformType.SQUARE:
        t_rise = waveform.pulse_width * 0.05
        return 0.35 / t_rise

    return waveform.repetition_rate * 10  # Fallback


def waveform_coefficient(waveform_type: WaveformType) -> float:
    """
    Return Kf equivalent for Faraday's law.
    V = Kf * f * N * Ae * Bpk

    Args:
        waveform_type: WaveformType enum

    Returns:
        Kf coefficient
    """
    if waveform_type == WaveformType.SINUSOIDAL:
        return 4.44
    elif waveform_type == WaveformType.SQUARE:
        return 4.0
    elif waveform_type == WaveformType.TRIANGULAR:
        return 4.0
    else:
        return 4.0
