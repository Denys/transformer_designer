"""
Winding calculations: turns, wire sizing, resistance
Based on McLyman's methodology

Includes:
- AWG wire selection
- Litz wire recommendation for high-frequency designs (>50kHz)
- Skin depth and proximity effect calculations
- DC and AC resistance estimation
"""

import math
from typing import Tuple, Optional, Literal, Dict

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
    41: (0.071, 0.00397, 0.0000397),
    42: (0.064, 0.00321, 0.0000321),
    43: (0.056, 0.00246, 0.0000246),
    44: (0.051, 0.00204, 0.0000204),
    45: (0.045, 0.00159, 0.0000159),
    46: (0.040, 0.00126, 0.0000126),
}

# Standard Litz wire bundle sizes (hex packing for round strands)
LITZ_BUNDLE_SIZES = [7, 19, 37, 65, 127, 259, 427, 741, 1050, 2100]

# Recommended strand gauges for Litz wire by frequency range
LITZ_STRAND_AWG_BY_FREQ = {
    # (min_freq_Hz, max_freq_Hz): recommended_strand_awg
    (20000, 50000): 40,      # 20-50 kHz: AWG 40 (0.08mm)
    (50000, 100000): 42,     # 50-100 kHz: AWG 42 (0.064mm)
    (100000, 200000): 44,    # 100-200 kHz: AWG 44 (0.051mm)
    (200000, 500000): 44,    # 200-500 kHz: AWG 44
    (500000, 1000000): 46,   # 500kHz-1MHz: AWG 46 (0.040mm)
    (1000000, 5000000): 46,  # 1-5 MHz: AWG 46
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
        "wire_type": "solid",
    }


def recommend_litz_wire(
    required_area_cm2: float,
    frequency_Hz: float,
    current_rms_A: float = None,
    max_strand_diameter_mm: float = None,
    optimization: Literal["loss", "cost", "size"] = "loss",
) -> Dict:
    """
    Recommend Litz wire configuration for high-frequency applications.
    
    Litz wire consists of many individually-insulated strands woven together
    to reduce skin and proximity effect losses at high frequencies.
    
    Rules of thumb:
    - Strand diameter should be ≤ 2 × skin depth for effective loss reduction
    - Common strand gauges: 38, 40, 42, 44, 46 AWG
    - Bundle in groups of 7, 19, 37, 65, 127... (hexagonal packing)
    - Effective at frequencies 20 kHz - 2 MHz
    
    Args:
        required_area_cm2: Required copper area [cm²]
        frequency_Hz: Operating frequency [Hz]
        current_rms_A: RMS current (optional, for loss estimation)
        max_strand_diameter_mm: Override for max strand diameter [mm]
        optimization: "loss" (lowest AC resistance), "cost" (fewer strands),
                     "size" (smallest bundle OD)
    
    Returns:
        Dict with Litz wire specification:
        - strand_awg: AWG of individual strands
        - strand_count: Number of strands
        - bundle_arrangement: How strands are grouped (e.g., "19x27")
        - outer_diameter_mm: Estimated bundle outer diameter
        - total_area_cm2: Total copper cross-section
        - ac_factor: Estimated RAC/RDC ratio (should be close to 1.0)
        - effective_at_frequency: Whether this Litz config is effective
        
    Reference:
        McLyman, Chapter 7 - Litz Wire
        Hurley & Wölfle, "Transformers and Inductors for Power Electronics"
    """
    if frequency_Hz < 10000:
        # Below 10kHz, solid wire is usually adequate
        return {
            "wire_type": "solid",
            "recommendation": "Frequency too low for Litz wire benefit",
            "threshold_Hz": 20000,
        }
    
    # Calculate skin depth
    skin_depth_mm = calculate_skin_depth(frequency_Hz)
    
    # Determine max strand diameter (should be < 2δ, ideally < 1.5δ)
    if max_strand_diameter_mm is None:
        # Conservative: strand ≤ 1.5 × skin depth
        max_strand_d = 1.5 * skin_depth_mm
        # Even more conservative for very high frequencies
        if frequency_Hz > 500000:
            max_strand_d = skin_depth_mm
    else:
        max_strand_d = min(max_strand_diameter_mm, 2 * skin_depth_mm)
    
    # Select strand AWG based on frequency range
    strand_awg = _select_litz_strand_awg(frequency_Hz, max_strand_d)
    strand_dia_mm, strand_area_mm2 = awg_to_mm(strand_awg)
    strand_area_cm2 = strand_area_mm2 / 100
    
    # Calculate required number of strands
    strands_needed = math.ceil(required_area_cm2 / strand_area_cm2)
    
    # Round up to standard bundle size
    bundle_size = _select_bundle_size(strands_needed, optimization)
    
    # Calculate actual total area
    total_area_cm2 = strand_area_cm2 * bundle_size
    
    # Estimate bundle outer diameter
    # For hexagonal packing, the number of strands across diameter ≈ sqrt(N * 4/π) * 0.866
    # Plus insulation and serving adds ~20-30%
    strands_across = math.sqrt(bundle_size * 4 / math.pi) * 0.866
    bundle_od_bare = strands_across * strand_dia_mm
    bundle_od_insulated = bundle_od_bare * 1.25  # ~25% for insulation and voids
    
    # Calculate estimated AC resistance factor
    # For well-designed Litz, RAC/RDC should be 1.0-1.3 at the design frequency
    ac_factor = _estimate_litz_ac_factor(strand_dia_mm, frequency_Hz, bundle_size)
    
    # Determine bundle arrangement string (e.g., "7x7x7" for 343 strands)
    arrangement = _describe_bundle_arrangement(bundle_size)
    
    # Check if this configuration is effective
    is_effective = (strand_dia_mm <= 2 * skin_depth_mm) and (ac_factor < 1.5)
    
    # Calculate resistance per meter (for reference)
    # Rdc per meter = ρ / A, where ρ for copper ≈ 1.72e-8 Ω·m
    rho_copper = 1.72e-8  # Ω·m
    Rdc_per_m_mOhm = (rho_copper / (total_area_cm2 * 1e-4)) * 1000  # mΩ/m
    
    # Estimate DC loss if current provided
    loss_estimate = None
    if current_rms_A is not None:
        # P = I²R per meter
        loss_per_m_W = (current_rms_A ** 2) * (Rdc_per_m_mOhm / 1000) * ac_factor
        loss_estimate = round(loss_per_m_W, 3)
    
    return {
        "wire_type": "litz",
        "strand_awg": strand_awg,
        "strand_diameter_mm": round(strand_dia_mm, 4),
        "strand_count": bundle_size,
        "bundle_arrangement": arrangement,
        "outer_diameter_mm": round(bundle_od_insulated, 2),
        "total_area_cm2": round(total_area_cm2, 6),
        "total_area_mm2": round(total_area_cm2 * 100, 4),
        "Rdc_mOhm_per_m": round(Rdc_per_m_mOhm, 3),
        "ac_factor": round(ac_factor, 3),
        "skin_depth_mm": round(skin_depth_mm, 4),
        "effective_at_frequency": is_effective,
        "loss_per_m_W": loss_estimate,
        "notes": _litz_notes(strand_awg, bundle_size, frequency_Hz, is_effective),
    }


def _select_litz_strand_awg(frequency_Hz: float, max_diameter_mm: float) -> int:
    """
    Select appropriate strand AWG based on frequency and max diameter.
    
    Returns AWG that satisfies both frequency recommendation and diameter limit.
    """
    # Find recommended AWG from frequency table
    recommended_awg = 40  # Default
    for (f_min, f_max), awg in LITZ_STRAND_AWG_BY_FREQ.items():
        if f_min <= frequency_Hz < f_max:
            recommended_awg = awg
            break
    else:
        if frequency_Hz >= 5000000:
            recommended_awg = 46
    
    # Check if recommended AWG fits within diameter limit
    for awg in range(recommended_awg, 47):
        dia_mm, _ = awg_to_mm(awg)
        if dia_mm <= max_diameter_mm:
            return awg
    
    # If nothing fits, use finest available
    return 46


def _select_bundle_size(strands_needed: int, optimization: str) -> int:
    """
    Select standard bundle size based on required strands and optimization goal.
    """
    if optimization == "cost":
        # Prefer smaller bundles (fewer strands = lower cost)
        for size in LITZ_BUNDLE_SIZES:
            if size >= strands_needed:
                return size
    elif optimization == "size":
        # Choose closest to minimize excess copper
        closest = min(LITZ_BUNDLE_SIZES, key=lambda s: abs(s - strands_needed))
        if closest >= strands_needed * 0.9:  # Allow up to 10% under
            return closest
        return min(s for s in LITZ_BUNDLE_SIZES if s >= strands_needed)
    else:  # optimization == "loss" or default
        # Allow some overhead for better fill factor
        for size in LITZ_BUNDLE_SIZES:
            if size >= strands_needed * 0.95:  # 5% margin OK for loss
                return size
    
    # If strands needed exceeds largest standard size, use multiple bundles
    return strands_needed


def _estimate_litz_ac_factor(strand_dia_mm: float, frequency_Hz: float, num_strands: int) -> float:
    """
    Estimate AC/DC resistance ratio for Litz wire.
    
    For well-designed Litz with proper twisting and strand size < 2δ,
    the AC factor should approach 1.0. In practice:
    - 1.0-1.1: Excellent (strand << skin depth)
    - 1.1-1.3: Good (strand < skin depth)
    - 1.3-1.5: Acceptable (strand ~ skin depth)
    - >1.5: Poor (strand > skin depth, losing Litz benefit)
    
    This is a simplified model; real performance depends on:
    - Twist pitch and pattern
    - Bundle arrangement (concentric vs. braided)
    - Proximity effects from adjacent windings
    """
    skin_depth_mm = calculate_skin_depth(frequency_Hz)
    d_delta = strand_dia_mm / skin_depth_mm
    
    # Skin effect contribution per strand
    if d_delta < 0.5:
        Fr_skin = 1.0
    elif d_delta < 1.0:
        Fr_skin = 1.0 + 0.1 * (d_delta ** 2)
    elif d_delta < 2.0:
        Fr_skin = 1.0 + 0.3 * (d_delta ** 2)
    else:
        Fr_skin = d_delta  # Losing Litz benefit
    
    # Proximity effect between strands (reduced by twisting)
    # Assume proper twisting reduces proximity by factor of ~10 vs. parallel wires
    if num_strands <= 19:
        Fr_prox = 1.0
    elif num_strands <= 65:
        Fr_prox = 1.0 + 0.02 * (d_delta ** 2)
    elif num_strands <= 259:
        Fr_prox = 1.0 + 0.05 * (d_delta ** 2)
    else:
        Fr_prox = 1.0 + 0.1 * (d_delta ** 2)
    
    return Fr_skin * Fr_prox


def _describe_bundle_arrangement(num_strands: int) -> str:
    """
    Describe the typical bundle arrangement for a given strand count.
    
    Common arrangements:
    - 7: 7×1 (one bunch of 7)
    - 19: 19×1
    - 49: 7×7 (bunched of 7, then bunched again)
    - 133: 19×7
    - 259: 37×7
    - 741: 19×39 or 7×106
    """
    arrangements = {
        7: "7×1",
        19: "19×1",
        37: "37×1",
        65: "65×1",
        127: "127×1",
        259: "37×7",
        427: "61×7",
        741: "19×39",
        1050: "7×150",
        2100: "7×300",
    }
    
    if num_strands in arrangements:
        return arrangements[num_strands]
    
    # For non-standard sizes, describe as single bunch
    return f"{num_strands}×1"


def _litz_notes(strand_awg: int, strand_count: int, frequency_Hz: float, is_effective: bool) -> str:
    """Generate helpful notes about the Litz wire selection."""
    notes = []
    
    if not is_effective:
        notes.append("⚠ Strands may be too large for this frequency. Consider finer gauge.")
    
    if strand_count > 741:
        notes.append("Large strand count - consider multiple parallel bundles.")
    
    if frequency_Hz > 1000000 and strand_awg < 44:
        notes.append("For MHz range, consider AWG 44-46 strands.")
    
    if strand_count < 19:
        notes.append("Small bundle - verify sufficient current capacity.")
    
    if not notes:
        notes.append("Good configuration for specified frequency.")
    
    return " ".join(notes)


def select_wire_for_frequency(
    required_area_cm2: float,
    frequency_Hz: float,
    prefer_litz_above_Hz: float = 50000,
) -> Dict:
    """
    Automatically select between solid wire and Litz wire based on frequency.
    
    Args:
        required_area_cm2: Required conductor area [cm²]
        frequency_Hz: Operating frequency [Hz]
        prefer_litz_above_Hz: Frequency threshold for Litz preference [Hz]
        
    Returns:
        Wire specification dict (either solid or Litz)
    """
    if frequency_Hz >= prefer_litz_above_Hz:
        litz_spec = recommend_litz_wire(required_area_cm2, frequency_Hz)
        if litz_spec.get("effective_at_frequency", False):
            return litz_spec
    
    # Fall back to solid wire with strand recommendation
    return select_wire_gauge(required_area_cm2, frequency_Hz)


def calculate_layers_from_geometry(
    num_turns: int,
    wire_diameter_mm: float,
    window_area_cm2: float,
    core_geometry: str = "E",
    fill_factor: float = 0.75,
) -> dict:
    """
    Calculate number of winding layers from window geometry.
    
    This replaces the crude Np//20 heuristic with geometry-aware calculation
    based on actual window dimensions and wire size.
    
    Args:
        num_turns: Total number of turns
        wire_diameter_mm: Wire diameter including insulation [mm]
        window_area_cm2: Core window area [cm²]
        core_geometry: Core shape family (E, ETD, PQ, etc.)
        fill_factor: Practical fill factor accounting for irregular packing (0.7-0.85)
        
    Returns:
        dict with:
            - num_layers: Number of layers
            - turns_per_layer: Turns fitting in one layer
            - bobbin_width_cm: Estimated bobbin winding width
            - window_height_cm: Estimated window height
            - layer_thickness_cm: Thickness of one layer
            
    Window geometry estimation:
        For E-cores: window is roughly 1.5:1 (height:width) ratio
        For PQ/pot cores: more square, ~1.2:1
        For toroids: use rectangular approximation
        
    Reference:
        McLyman Chapter 5 - practical winding layout considers:
        - Wire diameter + insulation (~10% increase)
        - Layer insulation (~0.1-0.2mm between layers)
        - Edge margins (~2mm on each end)
    """
    if num_turns <= 0 or wire_diameter_mm <= 0 or window_area_cm2 <= 0:
        return {
            "num_layers": 1,
            "turns_per_layer": num_turns,
            "bobbin_width_cm": 1.0,
            "window_height_cm": 1.0,
            "layer_thickness_cm": 0.1,
        }
    
    # Estimate window aspect ratio from core geometry
    geometry_upper = core_geometry.upper()
    
    if geometry_upper in ['E', 'EE', 'EI', 'ETD', 'ER', 'EQ', 'EFD', 'EP']:
        # E-type cores: tall window, aspect ratio ~1.5:1 (H:W)
        aspect_ratio = 1.5
    elif geometry_upper in ['PQ', 'PM', 'P', 'POT']:
        # Pot cores: more square window
        aspect_ratio = 1.2
    elif geometry_upper in ['RM']:
        # RM cores: low profile, wider window
        aspect_ratio = 0.8
    elif geometry_upper in ['T', 'TC', 'TOROID']:
        # Toroids: use rectangular approximation
        aspect_ratio = 1.0
    elif geometry_upper in ['U', 'UI', 'UU']:
        # U-cores: moderate aspect
        aspect_ratio = 1.3
    else:
        # Default: assume moderate aspect ratio
        aspect_ratio = 1.2
    
    # Calculate window dimensions
    # window_area = height × width
    # aspect_ratio = height / width
    # Therefore: width = sqrt(area / aspect_ratio)
    window_width_cm = math.sqrt(window_area_cm2 / aspect_ratio)
    window_height_cm = window_area_cm2 / window_width_cm
    
    # Account for bobbin margins and safety
    # Practical winding width ≈ 80-90% of window width
    margin_factor = 0.85
    bobbin_width_cm = window_width_cm * margin_factor
    
    # Wire effective diameter including insulation (typ. +10%)
    insulation_factor = 1.1
    wire_eff_dia_cm = (wire_diameter_mm / 10) * insulation_factor
    
    # Calculate turns per layer
    # Account for packing efficiency and edge spacing
    turns_per_layer = int(bobbin_width_cm / wire_eff_dia_cm * fill_factor)
    turns_per_layer = max(1, turns_per_layer)  # At least 1 turn per layer
    
    # Calculate number of layers
    num_layers = math.ceil(num_turns / turns_per_layer)
    
    # Layer thickness (wire dia + interlayer insulation)
    interlayer_insulation_cm = 0.01  # ~0.1mm typical
    layer_thickness_cm = wire_eff_dia_cm + interlayer_insulation_cm
    
    # Sanity check: total layer stack should fit in window height
    total_stack_height_cm = num_layers * layer_thickness_cm
    if total_stack_height_cm > window_height_cm * 0.9:
        # Winding won't fit - adjust calculation or warn
        # For now, recalculate assuming max layers that fit
        max_layers = int(window_height_cm * 0.9 / layer_thickness_cm)
        if max_layers > 0:
            num_layers = max_layers
            turns_per_layer = math.ceil(num_turns / num_layers)
    
    return {
        "num_layers": num_layers,
        "turns_per_layer": turns_per_layer,
        "bobbin_width_cm": round(bobbin_width_cm, 2),
        "window_height_cm": round(window_height_cm, 2),
        "window_width_cm": round(window_width_cm, 2),
        "layer_thickness_cm": round(layer_thickness_cm, 3),
        "total_stack_height_cm": round(num_layers * layer_thickness_cm, 2),
        "fill_factor_used": fill_factor,
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
