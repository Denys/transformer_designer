"""
Pulse transformer design calculations

Implements:
- Volt-second calculation and core sizing
- Pulse response analysis (rise time, droop, backswing)
- IEC 60664 insulation requirements
- Winding design for minimal leakage
"""

import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Vacuum permeability [H/m]
MU_0 = 4 * math.pi * 1e-7

# Copper resistivity at 20°C [Ω·m]
RHO_CU = 1.72e-8

# Speed of light [m/s] - for wave propagation estimates
C = 3e8


# ============================================================================
# Volt-Second Calculation
# ============================================================================

@dataclass
class VoltSecondResult:
    """Result of volt-second calculation."""
    volt_second_uVs: float      # V·µs
    volt_second_mVs: float      # mV·s
    required_Ae_cm2: float      # Minimum core area
    required_Ae_mm2: float      # Minimum core area
    Bmax_T: float               # Maximum flux density used
    primary_turns_min: int      # Minimum primary turns
    flux_swing_T: float         # Total flux swing ΔB


def calculate_volt_second(
    voltage_V: float,
    pulse_width_us: float,
    duty_cycle_percent: float = 50.0,
) -> float:
    """
    Calculate volt-second product for pulse transformer.
    
    V·t = volt-second product determines core size requirement.
    
    For square wave pulse:
        V·t = V × t_pulse
    
    For symmetrical drive (50% duty):
        Only half the flux swing is used per pulse
        
    Args:
        voltage_V: Pulse voltage [V]
        pulse_width_us: Pulse width [µs]
        duty_cycle_percent: Duty cycle [%]
        
    Returns:
        Volt-second product [V·µs]
    """
    # Basic volt-second
    Vt = voltage_V * pulse_width_us
    
    # For asymmetric duty cycles, adjust for reset time
    if duty_cycle_percent != 50.0:
        # With asymmetric duty, more volt-seconds may be needed
        # to ensure core resets properly
        duty = duty_cycle_percent / 100.0
        reset_factor = max(duty, 1 - duty) / 0.5
        Vt *= reset_factor
    
    return Vt


def calculate_core_area_from_volt_second(
    volt_second_uVs: float,
    Bmax_T: float = 0.2,
    primary_turns: int = 10,
    margin: float = 1.2,
) -> Tuple[float, int]:
    """
    Calculate required core area from volt-second requirement.
    
    From Faraday's law:
        V·t = N × Ae × ΔB
        Ae = V·t / (N × ΔB)
    
    For pulse transformers, we use the full swing ΔB = 2×Bmax
    (assuming bipolar reset) or ΔB = Bmax for unipolar.
    
    Args:
        volt_second_uVs: Volt-second product [V·µs]
        Bmax_T: Maximum flux density [T]
        primary_turns: Primary turns (starting point)
        margin: Design margin (1.2 = 20% margin)
        
    Returns:
        Tuple of (required Ae [cm²], adjusted primary turns)
    """
    # Convert units: V·µs to V·s
    Vt_Vs = volt_second_uVs * 1e-6
    
    # Flux swing - assume unidirectional pulse (conservative)
    delta_B = Bmax_T
    
    # Calculate Ae in m²
    Ae_m2 = (Vt_Vs * margin) / (primary_turns * delta_B)
    
    # Convert to cm²
    Ae_cm2 = Ae_m2 * 1e4
    
    # Check if Ae is reasonable, adjust turns if needed
    min_practical_Ae = 0.05  # 0.05 cm² minimum practical core
    max_practical_Ae = 5.0   # 5 cm² for pulse transformer is large
    
    adjusted_turns = primary_turns
    
    if Ae_cm2 < min_practical_Ae:
        # Core too small, reduce turns
        adjusted_turns = max(1, int(primary_turns * Ae_cm2 / min_practical_Ae))
        Ae_cm2 = min_practical_Ae
    elif Ae_cm2 > max_practical_Ae:
        # Core too large, increase turns
        adjusted_turns = int(primary_turns * Ae_cm2 / max_practical_Ae) + 1
        Ae_cm2 = (Vt_Vs * margin) / (adjusted_turns * delta_B) * 1e4
    
    return Ae_cm2, adjusted_turns


def design_for_volt_second(
    voltage_V: float,
    pulse_width_us: float,
    duty_cycle_percent: float = 50.0,
    Bmax_T: float = 0.2,
    initial_turns: int = 10,
) -> VoltSecondResult:
    """
    Complete volt-second based design.
    
    Args:
        voltage_V: Pulse voltage [V]
        pulse_width_us: Pulse width [µs]
        duty_cycle_percent: Duty cycle [%]
        Bmax_T: Maximum flux density [T]
        initial_turns: Starting number of turns
        
    Returns:
        VoltSecondResult with complete sizing
    """
    # Calculate volt-second
    Vt = calculate_volt_second(voltage_V, pulse_width_us, duty_cycle_percent)
    
    # Calculate required core area
    Ae_cm2, turns = calculate_core_area_from_volt_second(
        Vt, Bmax_T, initial_turns
    )
    
    return VoltSecondResult(
        volt_second_uVs=Vt,
        volt_second_mVs=Vt / 1000,
        required_Ae_cm2=round(Ae_cm2, 4),
        required_Ae_mm2=round(Ae_cm2 * 100, 2),
        Bmax_T=Bmax_T,
        primary_turns_min=turns,
        flux_swing_T=Bmax_T,  # Unidirectional
    )


# ============================================================================
# Pulse Response Analysis
# ============================================================================

@dataclass
class PulseResponse:
    """Pulse response characteristics."""
    rise_time_ns: float
    fall_time_ns: float
    droop_percent: float
    backswing_percent: float
    bandwidth_3dB_MHz: float
    ringing_freq_MHz: Optional[float]
    overshoot_percent: float


def calculate_rise_time(
    leakage_inductance_H: float,
    load_resistance_ohm: float,
    winding_capacitance_F: float,
) -> float:
    """
    Calculate pulse rise time.
    
    For a pulse transformer, rise time is limited by:
    1. L/R time constant (leakage inductance / load resistance)
    2. LC resonance with parasitic capacitance
    
    tr ≈ 2.2 × L_leak / R_load  (for overdamped)
    tr ≈ π × √(L_leak × C_wind) (for underdamped)
    
    Args:
        leakage_inductance_H: Leakage inductance [H]
        load_resistance_ohm: Load resistance [Ω]
        winding_capacitance_F: Winding capacitance [F]
        
    Returns:
        Rise time [s]
    """
    # L/R time constant based rise time
    tau_LR = leakage_inductance_H / load_resistance_ohm
    tr_LR = 2.2 * tau_LR  # 10-90% rise time
    
    # LC based rise time (quarter period of resonance)
    if winding_capacitance_F > 0:
        tr_LC = math.pi * math.sqrt(leakage_inductance_H * winding_capacitance_F)
    else:
        tr_LC = 0
    
    # Actual rise time is the larger of the two
    return max(tr_LR, tr_LC)


def calculate_droop(
    magnetizing_inductance_H: float,
    load_resistance_ohm: float,
    pulse_width_s: float,
) -> float:
    """
    Calculate pulse top droop.
    
    Droop occurs because magnetizing current increases during the pulse,
    reducing the current available to the load.
    
    For a step input:
        Droop ≈ (t_pulse × R_load) / L_mag × 100%
    
    More accurately:
        Droop ≈ (1 - exp(-t_pulse × R_load / L_mag)) × 100%
    
    Args:
        magnetizing_inductance_H: Magnetizing inductance [H]
        load_resistance_ohm: Load resistance [Ω]
        pulse_width_s: Pulse width [s]
        
    Returns:
        Droop percentage [%]
    """
    if magnetizing_inductance_H <= 0:
        return 100.0  # Complete droop
    
    tau = magnetizing_inductance_H / load_resistance_ohm
    
    # For short pulses (t << τ), linear approximation
    if pulse_width_s < tau / 10:
        droop = (pulse_width_s / tau) * 100
    else:
        # Exponential decay
        droop = (1 - math.exp(-pulse_width_s / tau)) * 100
    
    return min(droop, 100.0)


def calculate_backswing(
    magnetizing_inductance_H: float,
    leakage_inductance_H: float,
    winding_capacitance_F: float,
    pulse_voltage_V: float,
    pulse_width_s: float,
) -> Tuple[float, float]:
    """
    Calculate backswing voltage and ringing frequency.
    
    Backswing occurs when stored energy in magnetizing inductance
    resonates with winding capacitance after pulse ends.
    
    V_backswing ≈ I_mag × √(L_mag / C_wind)
    where I_mag = V × t_pulse / L_mag
    
    Args:
        magnetizing_inductance_H: Magnetizing inductance [H]
        leakage_inductance_H: Leakage inductance [H]
        winding_capacitance_F: Winding capacitance [F]
        pulse_voltage_V: Pulse voltage [V]
        pulse_width_s: Pulse width [s]
        
    Returns:
        Tuple of (backswing voltage [V], ringing frequency [Hz])
    """
    if winding_capacitance_F <= 0 or magnetizing_inductance_H <= 0:
        return 0.0, 0.0
    
    # Magnetizing current at end of pulse
    I_mag = pulse_voltage_V * pulse_width_s / magnetizing_inductance_H
    
    # Characteristic impedance
    Z0 = math.sqrt(magnetizing_inductance_H / winding_capacitance_F)
    
    # Backswing voltage
    V_backswing = I_mag * Z0
    
    # Ringing frequency (LC resonance)
    f_ring = 1 / (2 * math.pi * math.sqrt(magnetizing_inductance_H * winding_capacitance_F))
    
    return V_backswing, f_ring


def analyze_pulse_response(
    magnetizing_inductance_uH: float,
    leakage_inductance_nH: float,
    winding_capacitance_pF: float,
    load_resistance_ohm: float,
    pulse_voltage_V: float,
    pulse_width_us: float,
    load_inductance_nH: float = 0.0,
    load_capacitance_pF: float = 0.0,
) -> PulseResponse:
    """
    Complete pulse response analysis.
    
    Supports complex loads (R-L, R-C) via analytical approximations.

    Args:
        magnetizing_inductance_uH: Magnetizing inductance [µH]
        leakage_inductance_nH: Leakage inductance [nH]
        winding_capacitance_pF: Winding capacitance [pF]
        load_resistance_ohm: Load resistance [Ω]
        pulse_voltage_V: Pulse voltage [V]
        pulse_width_us: Pulse width [µs]
        load_inductance_nH: Load inductance [nH]
        load_capacitance_pF: Load capacitance [pF]
        
    Returns:
        PulseResponse analysis
    """
    # Convert units
    Lm = magnetizing_inductance_uH * 1e-6  # H
    Llk = leakage_inductance_nH * 1e-9      # H
    Cw = winding_capacitance_pF * 1e-12     # F
    t_pulse = pulse_width_us * 1e-6         # s
    L_load = load_inductance_nH * 1e-9      # H
    C_load = load_capacitance_pF * 1e-12    # F

    # Effective load inductance (adds to leakage for rise time)
    L_total_rise = Llk + L_load

    # Effective capacitance (winding + load)
    C_total = Cw + C_load
    
    # Rise/fall time with complex load
    # If L_load is significant, it dominates rise time (L/R)
    # If C_load is significant, it dominates rise time (RC)

    # 1. Inductive Rise Time (L_total / R)
    tau_LR = L_total_rise / load_resistance_ohm
    tr_LR = 2.2 * tau_LR

    # 2. Capacitive Rise Time (R * C_total) - if source impedance is low?
    # Actually, leakage inductance forms resonant circuit with C_total
    # LC rise time
    if C_total > 0:
        tr_LC = math.pi * math.sqrt(L_total_rise * C_total)
    else:
        tr_LC = 0

    # 3. RC Rise time (if leakage is small but C_load large)
    # This usually happens if source impedance is not zero, but here we assume ideal source driving transformer.
    # The transformer leakage is the source impedance.

    rise_time = max(tr_LR, tr_LC)
    fall_time = rise_time * 1.1
    
    # Droop
    # Load inductance helps maintain current -> less droop initially?
    # No, droop is Lm issue.
    # If C_load is large, it holds voltage -> less droop?
    # Generally droop is dominated by Lm.
    droop = calculate_droop(Lm, load_resistance_ohm, t_pulse)
    
    # Backswing
    V_back, f_ring = calculate_backswing(Lm, Llk, Cw, pulse_voltage_V, t_pulse) # Use Cw for ringing, load C might dampen or lower freq

    if C_total > Cw:
        # Adjust ringing frequency for total capacitance
        f_ring = 1 / (2 * math.pi * math.sqrt(Lm * C_total))
        # Backswing voltage might be lower
        Z0_new = math.sqrt(Lm / C_total)
        I_mag = pulse_voltage_V * t_pulse / Lm
        V_back = I_mag * Z0_new

    backswing_percent = (V_back / pulse_voltage_V) * 100 if pulse_voltage_V > 0 else 0
    
    # Bandwidth
    bandwidth_Hz = 0.35 / rise_time if rise_time > 0 else 1e9
    
    # Damping factor and overshoot
    # Use total L and C
    if L_total_rise > 0 and C_total > 0:
        Q = (1 / load_resistance_ohm) * math.sqrt(L_total_rise / C_total)
        if Q < 0.5:
            overshoot = 0
        elif Q < 1:
            overshoot = math.exp(-math.pi * Q / math.sqrt(1 - Q**2)) * 100
        else:
            overshoot = 100 * (1 - 1/Q)
    else:
        overshoot = 0
    
    return PulseResponse(
        rise_time_ns=round(rise_time * 1e9, 2),
        fall_time_ns=round(fall_time * 1e9, 2),
        droop_percent=round(droop, 2),
        backswing_percent=round(backswing_percent, 2),
        bandwidth_3dB_MHz=round(bandwidth_Hz / 1e6, 3),
        ringing_freq_MHz=round(f_ring / 1e6, 3) if f_ring > 0 else None,
        overshoot_percent=round(overshoot, 2),
    )


# ============================================================================
# Energy Transfer Analysis
# ============================================================================

@dataclass
class EnergyTransferResult:
    """Energy transfer efficiency result."""
    efficiency_percent: float
    energy_input_J: float
    energy_transferred_J: float
    energy_loss_J: float
    peak_current_A: float
    transfer_time_us: float


def calculate_energy_transfer_efficiency(
    primary_capacitance_F: float,
    primary_voltage_V: float,
    secondary_capacitance_F: float,
    leakage_inductance_H: float,
    primary_resistance_ohm: float,
    secondary_resistance_ohm: float,
    turns_ratio: float = 1.0,
    magnetizing_inductance_H: Optional[float] = None,
) -> EnergyTransferResult:
    """
    Calculate energy transfer efficiency for resonant charging.

    Assumes a C-L-C resonant transfer where the primary capacitor
    discharges into the secondary capacitor through the transformer
    leakage inductance (and any external inductance).

    Efficiency is limited by series resistance and magnetizing current losses.

    Args:
        primary_capacitance_F: Primary storage capacitance [F]
        primary_voltage_V: Initial primary voltage [V]
        secondary_capacitance_F: Secondary load capacitance [F]
        leakage_inductance_H: Total series inductance referred to primary [H]
        primary_resistance_ohm: Primary series resistance [Ω]
        secondary_resistance_ohm: Secondary series resistance [Ω]
        turns_ratio: Transformer turns ratio (Nsec/Npri)
        magnetizing_inductance_H: Magnetizing inductance referred to primary [H]

    Returns:
        EnergyTransferResult
    """
    # Reflect secondary values to primary side
    C_sec_ref = secondary_capacitance_F * (turns_ratio ** 2)
    R_sec_ref = secondary_resistance_ohm / (turns_ratio ** 2)
    R_total = primary_resistance_ohm + R_sec_ref

    # Equivalent series capacitance
    if primary_capacitance_F + C_sec_ref > 0:
        C_eq = (primary_capacitance_F * C_sec_ref) / (primary_capacitance_F + C_sec_ref)
    else:
        return EnergyTransferResult(0, 0, 0, 0, 0, 0)

    # Resonance frequency and characteristic impedance
    if leakage_inductance_H > 0 and C_eq > 0:
        omega = 1.0 / math.sqrt(leakage_inductance_H * C_eq)
        Z0 = math.sqrt(leakage_inductance_H / C_eq)

        # Transfer time (half period)
        t_transfer = math.pi / omega
    else:
        return EnergyTransferResult(0, 0, 0, 0, 0, 0)

    # Initial energy
    E_in = 0.5 * primary_capacitance_F * (primary_voltage_V ** 2)

    # Peak current (undamped approximation)
    # I_peak = V_pri / Z0
    # Ideally should account for damping, but for high efficiency designs Z0 >> R
    I_peak = primary_voltage_V / Z0

    # Resistive Energy loss approximation: E_loss = integral(I^2 * R * dt)
    # I(t) = I_peak * sin(omega * t)
    # integral(sin^2) from 0 to pi = pi/2
    # Energy loss = I_peak^2 * R * (pi / (2 * omega))
    #             = I_peak^2 * R * t_transfer / 2

    E_resistive = (I_peak ** 2) * R_total * t_transfer / 2

    # Magnetizing Energy Loss (Trapped energy)
    # Estimate volt-seconds during transfer
    # V_L_mag approx sinusoidal half-wave. Average voltage V_avg = 2/pi * V_peak
    # But V_pri drops. Let's approximate effective Volt-Seconds as V_pri * t_transfer * 0.637
    E_mag = 0.0
    if magnetizing_inductance_H and magnetizing_inductance_H > 0:
        Vt_eff = primary_voltage_V * t_transfer * 0.637
        I_mag_peak = Vt_eff / magnetizing_inductance_H
        E_mag = 0.5 * magnetizing_inductance_H * (I_mag_peak ** 2)

    total_loss = E_resistive + E_mag

    # Cap loss to available energy
    if total_loss > E_in:
        total_loss = E_in

    E_out = E_in - total_loss
    efficiency = (E_out / E_in) * 100 if E_in > 0 else 0

    return EnergyTransferResult(
        efficiency_percent=round(efficiency, 2),
        energy_input_J=round(E_in, 4),
        energy_transferred_J=round(E_out, 4),
        energy_loss_J=round(total_loss, 4),
        peak_current_A=round(I_peak, 2),
        transfer_time_us=round(t_transfer * 1e6, 3)
    )


# ============================================================================
# IEC 60664 Insulation Calculator
# ============================================================================

@dataclass
class InsulationRequirements:
    """IEC 60664 insulation requirements."""
    clearance_mm: float         # Through air [mm]
    creepage_mm: float          # Over surface [mm]
    solid_insulation_mm: float  # Solid insulation thickness [mm]
    impulse_withstand_kV: float # Impulse withstand voltage [kV]
    ac_withstand_Vrms: float    # AC withstand voltage [Vrms]
    recommended_materials: List[str]
    construction_notes: List[str]


# IEC 60664-1 Table F.2 - Impulse withstand voltages by overvoltage category
# Values in kV for mains voltage up to given value
IMPULSE_WITHSTAND_KV = {
    # (mains_voltage_max, overvoltage_category): impulse_withstand_kV
    (50, "I"): 0.33,   (50, "II"): 0.5,    (50, "III"): 0.8,   (50, "IV"): 1.5,
    (100, "I"): 0.5,   (100, "II"): 0.8,   (100, "III"): 1.5,  (100, "IV"): 2.5,
    (150, "I"): 0.8,   (150, "II"): 1.5,   (150, "III"): 2.5,  (150, "IV"): 4.0,
    (300, "I"): 1.5,   (300, "II"): 2.5,   (300, "III"): 4.0,  (300, "IV"): 6.0,
    (600, "I"): 2.5,   (600, "II"): 4.0,   (600, "III"): 6.0,  (600, "IV"): 8.0,
    (1000, "I"): 4.0,  (1000, "II"): 6.0,  (1000, "III"): 8.0, (1000, "IV"): 12.0,
}

# IEC 60664-1 Table F.4 - Clearances for basic insulation
# Values in mm for given impulse withstand voltage at PD2, altitude ≤2000m
CLEARANCE_TABLE_MM = {
    0.33: 0.01, 0.5: 0.04, 0.8: 0.1, 1.5: 0.5,
    2.5: 1.5, 4.0: 3.0, 6.0: 5.5, 8.0: 8.0, 12.0: 14.0,
}

# IEC 60664-1 Table F.5 - Creepage distances
# Values in mm for material group II, pollution degree 2
CREEPAGE_TABLE_MM = {
    # Working voltage (Vrms): creepage (mm)
    10: 0.025, 12.5: 0.025, 16: 0.025, 20: 0.025, 25: 0.025,
    32: 0.04, 40: 0.063, 50: 0.1, 63: 0.16, 80: 0.25,
    100: 0.4, 125: 0.5, 160: 0.63, 200: 0.8, 250: 1.0,
    320: 1.25, 400: 1.6, 500: 2.0, 630: 2.5, 800: 3.2,
    1000: 4.0, 1250: 5.0, 1600: 6.3, 2000: 8.0, 2500: 10.0,
}


def calculate_insulation_requirements(
    working_voltage_Vrms: float,
    insulation_type: str = "basic",
    overvoltage_category: str = "II",
    pollution_degree: int = 2,
    altitude_m: float = 2000,
    material_group: str = "II",
) -> InsulationRequirements:
    """
    Calculate IEC 60664 insulation requirements.
    
    Args:
        working_voltage_Vrms: Working voltage [Vrms]
        insulation_type: functional/basic/supplementary/double/reinforced
        overvoltage_category: I/II/III/IV
        pollution_degree: 1/2/3
        altitude_m: Installation altitude [m]
        material_group: I/II/IIIa/IIIb
        
    Returns:
        InsulationRequirements with all values
    """
    notes = []
    
    # Determine mains voltage level for table lookup
    mains_levels = [50, 100, 150, 300, 600, 1000]
    # Use max mains level if voltage exceeds all levels
    matching_levels = [v for v in mains_levels if v >= working_voltage_Vrms * 0.9]
    mains_voltage = min(matching_levels) if matching_levels else max(mains_levels)
    
    # Get impulse withstand voltage
    key = (mains_voltage, overvoltage_category)
    impulse_kV = IMPULSE_WITHSTAND_KV.get(key, 6.0)
    
    # For voltages > 1000V, scale impulse voltage
    if working_voltage_Vrms > 1000:
        scale_factor = working_voltage_Vrms / 1000
        impulse_kV *= scale_factor
        notes.append(f"High voltage ({working_voltage_Vrms}Vrms): scaled impulse {impulse_kV:.1f}kV")
    
    # Insulation type multipliers
    if insulation_type == "functional":
        impulse_kV *= 0.5  # Reduced for functional
        type_factor = 1.0
    elif insulation_type == "basic":
        type_factor = 1.0
    elif insulation_type == "supplementary":
        type_factor = 1.0
    elif insulation_type == "double":
        type_factor = 2.0
        impulse_kV *= 1.6  # Increased for double
    elif insulation_type == "reinforced":
        type_factor = 2.0
        impulse_kV *= 1.6
    else:
        type_factor = 1.0
    
    # Get clearance from table
    clearance_values = sorted(CLEARANCE_TABLE_MM.keys())
    matching_clearances = [v for v in clearance_values if v >= impulse_kV]
    impulse_for_lookup = min(matching_clearances) if matching_clearances else max(clearance_values)
    clearance_mm = CLEARANCE_TABLE_MM.get(impulse_for_lookup, 8.0)
    
    # For impulse > max table value, extrapolate
    if impulse_kV > max(clearance_values):
        # Rough rule: ~1mm per kV above 12kV
        clearance_mm = 14.0 + (impulse_kV - 12.0) * 1.0
    
    # Altitude correction (7% per 1000m above 2000m)
    if altitude_m > 2000:
        altitude_factor = 1 + 0.07 * ((altitude_m - 2000) / 1000)
        clearance_mm *= altitude_factor
        notes.append(f"Altitude correction: {altitude_factor:.2f}x for {altitude_m}m")
    
    # Double/reinforced insulation doubles clearance
    clearance_mm *= type_factor
    
    # Get creepage from table
    creepage_voltages = sorted(CREEPAGE_TABLE_MM.keys())
    matching_creepages = [v for v in creepage_voltages if v >= working_voltage_Vrms]
    voltage_for_lookup = min(matching_creepages) if matching_creepages else max(creepage_voltages)
    creepage_mm = CREEPAGE_TABLE_MM.get(voltage_for_lookup, 10.0)
    
    # For voltages > max table value, extrapolate
    if working_voltage_Vrms > max(creepage_voltages):
        # Rough rule: 4mm per 1000V above 2500V
        creepage_mm = 10.0 + (working_voltage_Vrms - 2500) / 1000 * 4.0
    
    # Material group adjustment
    if material_group == "I":
        creepage_mm *= 0.8  # Better tracking resistance
    elif material_group == "IIIa":
        creepage_mm *= 1.25
    elif material_group == "IIIb":
        creepage_mm *= 1.6
    
    # Pollution degree adjustment
    if pollution_degree == 1:
        creepage_mm *= 0.8
    elif pollution_degree == 3:
        creepage_mm *= 1.6
        notes.append("PD3: Consider conformal coating")
    
    # Double/reinforced doubles creepage
    creepage_mm *= type_factor
    
    # Solid insulation thickness (rule of thumb)
    # Typically 0.4mm per kV for basic, more for reinforced
    solid_mm = max(0.1, impulse_kV * 0.4 * type_factor)
    
    # AC withstand voltage (typically 2× working + 1000V for basic)
    ac_withstand = working_voltage_Vrms * 2 + 1000
    if insulation_type in ["double", "reinforced"]:
        ac_withstand *= 1.5
    
    # Recommended materials
    materials = []
    if insulation_type in ["functional", "basic"]:
        materials = ["Polyimide (Kapton)", "Polyester (Mylar)", "Nomex"]
    else:
        materials = ["Triple-insulated wire", "Polyimide tape (3 layers)", "Silicone-coated fiberglass"]
    
    # Construction notes
    if insulation_type == "reinforced":
        notes.append("Use triple-insulated wire OR 3 layers of insulation tape")
        notes.append("Each layer must meet basic insulation requirements")
    
    notes.append(f"Minimum creepage path: {creepage_mm:.2f}mm")
    notes.append(f"Minimum clearance: {clearance_mm:.2f}mm")
    
    return InsulationRequirements(
        clearance_mm=round(clearance_mm, 2),
        creepage_mm=round(creepage_mm, 2),
        solid_insulation_mm=round(solid_mm, 2),
        impulse_withstand_kV=round(impulse_kV, 1),
        ac_withstand_Vrms=round(ac_withstand, 0),
        recommended_materials=materials,
        construction_notes=notes,
    )


# ============================================================================
# Magnetizing Inductance Calculation
# ============================================================================

def calculate_magnetizing_inductance(
    turns: int,
    Ae_m2: float,
    lm_m: float,
    mu_r: float = 2000,
    air_gap_m: float = 0,
) -> float:
    """
    Calculate magnetizing inductance.
    
    L = µ0 × µr × N² × Ae / le
    
    With air gap:
    L = µ0 × N² × Ae / (le/µr + lg)
    
    Args:
        turns: Number of turns
        Ae_m2: Effective area [m²]
        lm_m: Magnetic path length [m]
        mu_r: Relative permeability
        air_gap_m: Air gap length [m]
        
    Returns:
        Inductance [H]
    """
    if air_gap_m > 0:
        # With air gap, permeability is dominated by gap
        reluctance = lm_m / (MU_0 * mu_r * Ae_m2) + air_gap_m / (MU_0 * Ae_m2)
        L = turns * turns / reluctance
    else:
        # No gap
        L = MU_0 * mu_r * turns * turns * Ae_m2 / lm_m
    
    return L


def calculate_leakage_inductance(
    turns: int,
    MLT_m: float,
    winding_height_m: float,
    winding_width_m: float,
    layer_spacing_m: float,
    num_layers: int = 2,
) -> float:
    """
    Calculate leakage inductance (simplified Dowell model).
    
    L_leak ≈ µ0 × N² × MLT × (h_cu/3 + s) / w
    
    where:
    - h_cu = copper height per layer
    - s = spacing between layers
    - w = winding width
    
    Args:
        turns: Number of turns
        MLT_m: Mean length per turn [m]
        winding_height_m: Total winding height [m]
        winding_width_m: Winding width [m]
        layer_spacing_m: Layer spacing [m]
        num_layers: Number of layers
        
    Returns:
        Leakage inductance [H]
    """
    # Copper height per layer
    h_cu = winding_height_m / num_layers if num_layers > 0 else winding_height_m
    
    # Effective leakage path
    leakage_path = h_cu / 3 + layer_spacing_m * (num_layers - 1)
    
    L_leak = MU_0 * turns * turns * MLT_m * leakage_path / winding_width_m
    
    return L_leak


def calculate_winding_capacitance(
    turns: int,
    MLT_m: float,
    wire_diameter_m: float,
    layer_spacing_m: float,
    insulation_thickness_m: float,
    epsilon_r: float = 3.5,  # Typical for polyimide
    num_layers: int = 2,
) -> float:
    """
    Calculate winding capacitance (layer-to-layer and turn-to-turn).
    
    C ≈ ε0 × εr × A / d
    
    Args:
        turns: Number of turns
        MLT_m: Mean length per turn [m]
        wire_diameter_m: Wire diameter [m]
        layer_spacing_m: Layer spacing [m]
        insulation_thickness_m: Insulation thickness [m]
        epsilon_r: Relative permittivity
        num_layers: Number of layers
        
    Returns:
        Capacitance [F]
    """
    epsilon_0 = 8.854e-12  # F/m
    
    # Turn-to-turn capacitance (simplified)
    # Area = length × wire_diameter, gap = insulation
    turns_per_layer = turns / num_layers if num_layers > 0 else turns
    Ctt = epsilon_0 * epsilon_r * MLT_m * wire_diameter_m / insulation_thickness_m
    
    # Layer-to-layer capacitance
    if num_layers > 1:
        # Area = MLT × winding_width, gap = layer_spacing
        layer_area = MLT_m * (turns_per_layer * wire_diameter_m)
        Cll = epsilon_0 * epsilon_r * layer_area / layer_spacing_m * (num_layers - 1)
    else:
        Cll = 0
    
    # Total capacitance (series/parallel combination - simplified)
    C_total = Ctt * turns_per_layer / 3 + Cll / 2
    
    return C_total