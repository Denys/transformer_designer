import pytest
import math
from calculations.waveform import WaveformType, PulseWaveform, calculate_volt_seconds, calculate_rms_voltage, calculate_effective_frequency
from calculations.insulation import winding_build_hv, recommend_insulation_system
from calculations.winding import wire_selection_high_current, foil_winding_design, effective_frequency_pulse
from calculations.thermal import thermal_pulsed_operation

def test_waveform_calculations():
    # Square wave
    pulse = PulseWaveform(
        waveform_type=WaveformType.SQUARE,
        peak_voltage=100,
        pulse_width=10e-6,
        rise_time=1e-6,
        fall_time=1e-6,
        repetition_rate=10e3
    )

    vs = calculate_volt_seconds(pulse)
    assert vs == 100 * 10e-6

    rms = calculate_rms_voltage(pulse)
    # D = 0.1. RMS = 100 * sqrt(0.1) = 31.62
    assert math.isclose(rms, 100 * math.sqrt(0.1), rel_tol=1e-3)

    freq = calculate_effective_frequency(pulse)
    # 0.35 / 1e-6 = 350 kHz
    assert math.isclose(freq, 350000, rel_tol=1e-3)

def test_hv_winding_build():
    build = winding_build_hv(
        turns=100,
        wire_diameter_mm=0.5,
        bobbin_winding_length_mm=50,
        bobbin_winding_depth_mm=10,
        required_creepage_mm=4.0
    )

    assert build.is_feasible
    # Margin 4mm each side -> 42mm effective width
    # Turns per layer = 42 / 0.5 * 0.9 = 75
    assert build.turns_per_layer == 75
    # Layers = ceil(100/75) = 2
    assert build.num_layers == 2
    assert build.margin_tape_width_mm == 4.0

def test_high_current_wire_selection():
    # High current, low freq -> should recommend foil or parallel round
    # 100A, 50kHz
    selection = wire_selection_high_current(
        current_peak_A=100,
        current_rms_A=70,
        frequency_Hz=50000,
        current_density_A_cm2=500
    )

    rec = selection["recommended"]
    # At 50kHz, skin depth ~0.3mm. Foil 0.3-0.5mm is good.
    # Litz is also good above 20kHz.
    # Logic prefers Litz > 100kHz.
    # Logic prefers foil > 20A & < 100kHz.
    assert rec["type"] == "foil"
    assert "thickness_mm" in rec
    assert "width_mm" in rec

def test_pulsed_thermal():
    thermal = thermal_pulsed_operation(
        peak_power=1000,
        average_power=50,
        pulse_width=1e-3,
        duty_cycle=0.01,
        thermal_mass=10.0, # J/C
        thermal_resistance=2.0 # C/W
    )

    # Avg rise = 50 * 2 = 100 C
    assert thermal["temp_rise_average_C"] == 100

    # Pulse rise = 1000 * 1e-3 / 10 = 0.1 C
    assert math.isclose(thermal["temp_rise_pulse_C"], 0.1, rel_tol=1e-5)

    assert thermal["temp_peak_rise_C"] == 100.1
