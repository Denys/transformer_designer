"""
Winding calculations: turns, wire sizing, resistance
Based on McLyman's methodology
"""

import math
from typing import Tuple, Optional, Literal

# Copper resistivity at 20°C [Ω·cm]
RHO_COPPER_20C = 1.724e-6

# Temperature coefficient of copper [/°C]
ALPHA_COPPER = 0.00393


# AWG wire table: AWG -> (diameter_mm, area_mm2, area_cm2)
AWG_TABLE = {
    0: (8.251, 53.48, 0.5348),
    1: (7.348, 42.41, 0.4241),
    2: (6.544, 33.63, 0.3363),
    3: (5.827, 26.67, 0.2667),
    4: (5.189, 21.15, 0.2115),
    5: (4.621, 16.77, 0.1677),
    6: (4.115, 13.30, 0.1330),
    7: (3.665, 10.55, 0.1055),
    8: (3.264, 8.366, 0.08366),
    9: (2.906, 6.632, 0.06632),
    10: (2.588, 5.261, 0.05261),
    11: (2.305, 4.172, 0.04172),
    12: (2.053, 3.309, 0.03309),
    13: (1.828, 2.624, 0.02624),
    14: (1.628, 2.081, 0.02081),
    15: (1.450, 1.650, 0.01650),
    16: (1.291, 1.309, 0.01309),
    17: (1.150, 1.038, 0.01038),
    18: (1.024, 0.823, 0.00823),
    19: (0.912, 0.653, 0.00653),
    20: (0.812, 0.518, 0.00518),
    21: (0.723, 0.411, 0.00411),
    22: (0.644, 0.326, 0.00326),
    23: (0.573, 0.258, 0.00258),
    24: (0.511, 0.205, 0.00205),
    25: (0.455, 0.162, 0.00162),
    26: (0.405, 0.129, 0.00129),
    27: (0.361, 0.102, 0.00102),
    28: (0.321, 0.0810, 0.000810),
    29: (0.286, 0.0642, 0.000642),
    30: (0.255, 0.0509, 0.000509),
    31: (0.227, 0.0404, 0.000404),
    32: (0.202, 0.0320, 0.000320),
    33: (0.180, 0.0254, 0.000254),
    34: (0.160, 0.0201, 0.000201),
    35: (0.143, 0.0160, 0.000160),
    36: (0.127, 0.0127, 0.000127),
    37: (0.113, 0.0100, 0.000100),
    38: (0.101, 0.00797, 0.0000797),
    39: (0.090, 0.00632, 0.0000632),
    40: (0.080, 0.00501, 0.0000501),
}


def awg_to_mm(awg: int) -> Tuple[float, float]:
    """
    Convert AWG to wire diameter and area.
    
    Args:
        awg: American Wire Gauge number (0-40)
        
    Returns:
        Tuple of (diameter_mm, area_mm2)
    """
    if awg not in AWG_TABLE:
        # Calculate from formula if not in table
        diameter_mm = 0.127 * (92 ** ((36 - awg) / 39))
        area_mm2 = math.pi * (diameter_mm / 2) ** 2
        return (diameter_mm, area_mm2)
    
    return AWG_TABLE[awg][:2]


def mm_to_awg(diameter_mm: float) -> int:
    """
    Find closest AWG for a given wire diameter.
    
    Args:
        diameter_mm: Wire diameter [mm]
        
    Returns:
        Closest AWG number
    """
    # AWG formula: d = 0.127 × 92^((36-n)/39)
    # Solve for n: n = 36 - 39 × log(d/0.127) / log(92)
    if diameter_mm <= 0:
        raise ValueError("Diameter must be positive")
    
    n = 36 - 39 * math.log(diameter_mm / 0.127) / math.log(92)
    awg = round(n)
    
    # Clamp to valid range
    return max(0, min(40, awg))


def calculate_wire_area(current_rms_A: float, current_density_A_cm2: float) -> float:
    """
    Calculate required wire cross-sectional area.
    
    Args:
        current_rms_A: RMS current [A]
        current_density_A_cm2: Target current density [A/cm²]
        
    Returns:
        Required wire area [cm²]
        
    Formula:
        Aw = Irms / J
    """
    if current_rms_A < 0 or current_density_A_cm2 <= 0:
        raise ValueError("Current must be non-negative and density must be positive")
    
    return current_rms_A / current_density_A_cm2


def select_wire_gauge(
    required_area_cm2: float,
    frequency_Hz: float = 0,
    max_awg: int = 40,
) -> dict:
    """
    Select wire gauge for required area, considering skin effect.
    
    Args:
        required_area_cm2: Required conductor area [cm²]
        frequency_Hz: Operating frequency for skin effect check [Hz]
        max_awg: Maximum AWG to consider (smaller wire)
        
    Returns:
        dict with wire selection details
    """
    # Calculate skin depth for frequency check
    skin_depth_mm = calculate_skin_depth(frequency_Hz) if frequency_Hz > 0 else float('inf')
    max_wire_dia_mm = 2 * skin_depth_mm  # Wire diameter should be < 2δ
    
    # Find smallest AWG that provides enough area
    for awg in range(max_awg, -1, -1):  # Start from small wire, go up
        dia_mm, area_mm2 = awg_to_mm(awg)
        area_cm2 = area_mm2 / 100  # Convert mm² to cm²
        
        if area_cm2 >= required_area_cm2:
            # Check if wire diameter is acceptable for frequency
            strands = 1
            if frequency_Hz > 0 and dia_mm > max_wire_dia_mm:
                # Need to use smaller wire with multiple strands
                # Find AWG that fits within skin depth limit
                for strand_awg in range(max_awg, awg, -1):
                    strand_dia_mm, strand_area_mm2 = awg_to_mm(strand_awg)
                    if strand_dia_mm <= max_wire_dia_mm:
                        strand_area_cm2 = strand_area_mm2 / 100
                        strands = math.ceil(required_area_cm2 / strand_area_cm2)
                        return {
                            "awg": strand_awg,
                            "diameter_mm": strand_dia_mm,
                            "area_cm2": strand_area_cm2 * strands,
                            "strands": strands,
                            "skin_effect_limited": True,
                            "skin_depth_mm": skin_depth_mm,
                        }
            
            return {
                "awg": awg,
                "diameter_mm": dia_mm,
                "area_cm2": area_cm2,
                "strands": strands,
                "skin_effect_limited": False,
                "skin_depth_mm": skin_depth_mm,
            }
    
    # If we get here, need multiple strands of smallest wire
    awg = max_awg
    dia_mm, area_mm2 = awg_to_mm(awg)
    area_cm2 = area_mm2 / 100
    strands = math.ceil(required_area_cm2 / area_cm2)
    
    return {
        "awg": awg,
        "diameter_mm": dia_mm,
        "area_cm2": area_cm2 * strands,
        "strands": strands,
        "skin_effect_limited": frequency_Hz > 0,
        "skin_depth_mm": skin_depth_mm,
    }


def calculate_turns(
    voltage_V: float,
    frequency_Hz: float,
    Bac_T: float,
    Ae_cm2: float,
    Kf: float = 4.44,
) -> int:
    """
    Calculate number of turns using Faraday's law.
    
    Args:
        voltage_V: Voltage (RMS for AC, or V for pulse)
        frequency_Hz: Operating frequency [Hz]
        Bac_T: AC flux density [T]
        Ae_cm2: Effective core area [cm²]
        Kf: Waveform coefficient (4.44 for sine, 4.0 for square)
        
    Returns:
        Number of turns (rounded up)
        
    Formula:
        N = (V × 10⁴) / (Kf × Bac × f × Ae)
        
    Reference:
        McLyman, Eq. 5-6
    """
    if any(v <= 0 for v in [voltage_V, frequency_Hz, Bac_T, Ae_cm2]):
        raise ValueError("All parameters must be positive")
    
    N = (voltage_V * 1e4) / (Kf * Bac_T * frequency_Hz * Ae_cm2)
    
    return math.ceil(N)


def calculate_skin_depth(frequency_Hz: float, temperature_C: float = 20) -> float:
    """
    Calculate skin depth for copper at given frequency.
    
    Args:
        frequency_Hz: Frequency [Hz]
        temperature_C: Temperature [°C]
        
    Returns:
        Skin depth δ [mm]
        
    Formula:
        δ = √(ρ / (π × f × μ₀))
        
    Simplified for copper:
        δ ≈ 66.2 / √f [mm] at 20°C
        
    Reference:
        McLyman, Eq. 7-3
    """
    if frequency_Hz <= 0:
        return float('inf')
    
    # Temperature correction for resistivity
    rho_factor = 1 + ALPHA_COPPER * (temperature_C - 20)
    
    # Skin depth in mm (derived from δ = √(ρ/(π×f×μ₀)))
    # At 20°C: δ = 66.2/√f [mm]
    delta_mm = 66.2 / math.sqrt(frequency_Hz) * math.sqrt(rho_factor)
    
    return delta_mm


def calculate_dc_resistance(
    turns: int,
    MLT_cm: float,
    wire_area_cm2: float,
    temperature_C: float = 20,
) -> float:
    """
    Calculate DC winding resistance.
    
    Args:
        turns: Number of turns
        MLT_cm: Mean length per turn [cm]
        wire_area_cm2: Wire cross-sectional area [cm²]
        temperature_C: Operating temperature [°C]
        
    Returns:
        DC resistance [Ω]
        
    Formula:
        Rdc = ρ × MLT × N / Aw
        
    Reference:
        McLyman, Eq. 5-14
    """
    if wire_area_cm2 <= 0:
        raise ValueError("Wire area must be positive")
    
    # Total wire length [cm]
    length_cm = turns * MLT_cm
    
    # Resistivity at temperature [Ω·cm]
    rho = RHO_COPPER_20C * (1 + ALPHA_COPPER * (temperature_C - 20))
    
    # DC resistance [Ω]
    Rdc = rho * length_cm / wire_area_cm2
    
    return Rdc


def calculate_ac_resistance_factor(
    wire_diameter_mm: float,
    frequency_Hz: float,
    num_layers: int = 1,
    temperature_C: float = 100,
) -> float:
    """
    Calculate AC/DC resistance ratio due to skin and proximity effects.
    
    Args:
        wire_diameter_mm: Wire diameter [mm]
        frequency_Hz: Operating frequency [Hz]
        num_layers: Number of winding layers
        temperature_C: Operating temperature [°C]
        
    Returns:
        Fr: RAC/RDC ratio
        
    Formula (Dowell approximation):
        For round wire with d < 2δ:
        Fr_skin ≈ 1 + (d/2δ)⁴ / 3
        Fr_prox ≈ 1 + (n²/3) × (d/δ)⁴
        
    Reference:
        McLyman, Chapter 7
    """
    if frequency_Hz <= 0:
        return 1.0
    
    delta_mm = calculate_skin_depth(frequency_Hz, temperature_C)
    
    # Ratio of wire diameter to skin depth
    d_delta = wire_diameter_mm / delta_mm
    
    if d_delta < 0.5:
        # Wire much smaller than skin depth - minimal AC effect
        return 1.0
    
    # Skin effect factor (valid for d < 2δ)
    if d_delta <= 2:
        Fr_skin = 1 + (d_delta ** 4) / 48
    else:
        # For d > 2δ, more complex formula needed
        Fr_skin = d_delta / 2  # Simplified high-frequency limit
    
    # Proximity effect factor
    if num_layers <= 1:
        Fr_prox = 1.0
    else:
        # Dowell approximation for multiple layers
        Fr_prox = 1 + ((num_layers ** 2 - 1) / 3) * (d_delta ** 4) / 48
    
    # Total AC resistance factor
    Fr = Fr_skin * Fr_prox
    
    # Sanity check - Fr should be at least 1
    return max(1.0, Fr)


def calculate_window_utilization(
    primary_turns: int,
    primary_wire_area_cm2: int,
    secondary_turns: int,
    secondary_wire_area_cm2: float,
    window_area_cm2: float,
    insulation_factor: float = 1.3,
) -> dict:
    """
    Calculate window utilization Ku.
    
    Args:
        primary_turns: Primary turns
        primary_wire_area_cm2: Primary wire area [cm²]
        secondary_turns: Secondary turns
        secondary_wire_area_cm2: Secondary wire area [cm²]
        window_area_cm2: Core window area [cm²]
        insulation_factor: Factor for insulation (1.2-1.5)
        
    Returns:
        dict with utilization details
    """
    # Total copper area
    primary_area = primary_turns * primary_wire_area_cm2
    secondary_area = secondary_turns * secondary_wire_area_cm2
    total_copper = (primary_area + secondary_area) * insulation_factor
    
    Ku = total_copper / window_area_cm2
    
    status = "ok"
    if Ku > 0.6:
        status = "error"
    elif Ku > 0.45:
        status = "warning"
    
    return {
        "Ku": Ku,
        "primary_area_cm2": primary_area,
        "secondary_area_cm2": secondary_area,
        "total_with_insulation_cm2": total_copper,
        "status": status,
    }
