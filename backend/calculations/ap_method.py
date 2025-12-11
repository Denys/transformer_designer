"""
Area Product (Ap) Method for transformer and inductor sizing
Based on McLyman's methodology

Ap = Ae × Wa [cm⁴]
Where:
    Ae = Effective core cross-sectional area [cm²]
    Wa = Window area [cm²]
"""

import math
from typing import Literal


def waveform_coefficient(waveform: Literal["sinusoidal", "square", "triangular"]) -> float:
    """
    Return waveform coefficient Kf for Faraday's law.
    
    Args:
        waveform: Type of input waveform
        
    Returns:
        Kf: Waveform coefficient
        
    Reference:
        McLyman, Table 5-1
        - Sinusoidal: Kf = 4.44
        - Square wave: Kf = 4.0
        - Triangular: Kf = 4.0
    """
    coefficients = {
        "sinusoidal": 4.44,
        "square": 4.0,
        "triangular": 4.0,
    }
    return coefficients.get(waveform, 4.44)


def calculate_bac_from_waveform(
    Bmax_T: float,
    waveform: Literal["sinusoidal", "square", "triangular", "trapezoidal"],
    duty_cycle: float = 0.5,
) -> float:
    """
    Calculate AC flux density swing (Bac) based on waveform type.
    
    For transformers, Bac is the peak-to-peak flux swing divided by 2.
    This is NOT simply Bmax/2 for all waveforms!
    
    Args:
        Bmax_T: Maximum flux density [T]
        waveform: Waveform type
        duty_cycle: Duty cycle for asymmetric waveforms (0-1)
        
    Returns:
        Bac: AC flux density for core loss calculations [T]
        
    Waveform-specific calculations:
        - Sinusoidal: Bac = Bmax (Bmax is the peak value)
        - Square: Bac = Bmax (full swing from -Bmax to +Bmax)
        - Triangular: Bac = Bmax (linear swing)
        - Trapezoidal: Bac = Bmax × (depends on duty cycle)
        
    For core loss calculations using Steinmetz equation:
        P_v = k × f^α × B_ac^β
        
    Reference:
        McLyman Chapter 4, Erickson "Fundamentals of Power Electronics"
        - For transformers: flux swings full ±Bpk range
        - For PWM/forward converters: flux resets, use actual ΔB
    """
    if Bmax_T <= 0:
        raise ValueError("Bmax must be positive")
    
    if not 0 < duty_cycle <= 1.0:
        raise ValueError("Duty cycle must be between 0 and 1")
    
    if waveform == "sinusoidal":
        # For sinusoidal, Bmax is the peak value
        # Core loss uses RMS-equivalent: Bac = Bmax
        return Bmax_T
    
    elif waveform == "square":
        # Square wave: full swing from -Bmax to +Bmax
        # Total swing = 2 × Bmax, but Bac for Steinmetz = Bmax
        return Bmax_T
    
    elif waveform == "triangular":
        # Triangular wave: linear rise/fall
        # Bac = Bmax for symmetric triangular
        return Bmax_T
    
    elif waveform == "trapezoidal":
        # Trapezoidal (PWM-like): depends on duty cycle
        # For D=0.5 (symmetric): Bac ≈ Bmax
        # For D!=0.5: Bac varies with duty
        # Simplified model: Bac = Bmax × (1 - |0.5 - D|/0.5)
        # This gives Bac=Bmax at D=0.5, reduces for extreme duties
        duty_factor = 1.0 - abs(0.5 - duty_cycle) / 0.5
        return Bmax_T * duty_factor
    
    else:
        # Default fallback: assume full swing
        return Bmax_T


def calculate_apparent_power(
    output_power_W: float,
    efficiency_percent: float = 90.0,
) -> float:
    """
    Calculate transformer apparent power (VA) from output power and efficiency.
    
    Args:
        output_power_W: Output power [W]
        efficiency_percent: Efficiency [%]
        
    Returns:
        Pt: Apparent power [VA]
        
    Formula:
        Pt = Po × (1 + 1/η)
        
    Reference:
        McLyman, Eq. 5-3
    """
    eta = efficiency_percent / 100.0
    
    if eta <= 0 or eta > 1:
        raise ValueError(f"Efficiency must be between 0 and 100%, got {efficiency_percent}%")
    
    # Apparent power includes both input and output
    Pt = output_power_W * (1 + 1/eta)
    
    return Pt


def calculate_area_product(
    apparent_power_VA: float,
    frequency_Hz: float,
    Bmax_T: float,
    current_density_A_cm2: float,
    Ku: float = 0.35,
    Kf: float = 4.44,
) -> float:
    """
    Calculate required Area Product (Ap) for transformer.
    
    Args:
        apparent_power_VA: Apparent power Pt [VA]
        frequency_Hz: Operating frequency [Hz]
        Bmax_T: Maximum flux density [T]
        current_density_A_cm2: Current density J [A/cm²]
        Ku: Window utilization factor (0.25-0.55)
        Kf: Waveform coefficient (4.44 for sine, 4.0 for square)
        
    Returns:
        Ap: Required area product [cm⁴]
        
    Formula:
        Ap = (Pt × 10⁴) / (Kf × Ku × Bm × J × f)
        
    Reference:
        McLyman, Eq. 5-1 and Eq. 5-7
    """
    if any(v <= 0 for v in [apparent_power_VA, frequency_Hz, Bmax_T, current_density_A_cm2]):
        raise ValueError("All input parameters must be positive")
    
    if not 0.1 <= Ku <= 0.8:
        raise ValueError(f"Ku should be between 0.1 and 0.8, got {Ku}")
    
    # Calculate Ap in cm⁴
    Ap = (apparent_power_VA * 1e4) / (Kf * Ku * Bmax_T * current_density_A_cm2 * frequency_Hz)
    
    return Ap


def calculate_area_product_inductor(
    inductance_H: float,
    peak_current_A: float,
    Bmax_T: float,
    current_density_A_cm2: float,
    Ku: float = 0.35,
) -> float:
    """
    Calculate required Area Product (Ap) for inductor using energy method.
    
    Args:
        inductance_H: Required inductance [H]
        peak_current_A: Peak current [A]
        Bmax_T: Maximum flux density [T]
        current_density_A_cm2: Current density J [A/cm²]
        Ku: Window utilization factor
        
    Returns:
        Ap: Required area product [cm⁴]
        
    Formula:
        Energy = 0.5 × L × Ipk²  [J]
        Ap = (2 × Energy × 10⁴) / (Bm × J × Ku)
        
    Reference:
        McLyman, Chapter 6, Energy Storage Method
    """
    if any(v <= 0 for v in [inductance_H, peak_current_A, Bmax_T, current_density_A_cm2]):
        raise ValueError("All input parameters must be positive")
    
    # Calculate stored energy [J]
    energy_J = 0.5 * inductance_H * peak_current_A ** 2
    
    # Calculate Ap in cm⁴
    Ap = (2 * energy_J * 1e4) / (Bmax_T * current_density_A_cm2 * Ku)
    
    return Ap


def calculate_current_density_from_ap(
    apparent_power_VA: float,
    frequency_Hz: float,
    Bmax_T: float,
    Ap_cm4: float,
    Ku: float = 0.35,
    Kf: float = 4.44,
) -> float:
    """
    Calculate current density given a specific core Ap.
    
    This is the inverse of calculate_area_product, used when
    a core is already selected.
    
    Args:
        apparent_power_VA: Apparent power [VA]
        frequency_Hz: Operating frequency [Hz]
        Bmax_T: Maximum flux density [T]
        Ap_cm4: Core area product [cm⁴]
        Ku: Window utilization factor
        Kf: Waveform coefficient
        
    Returns:
        J: Current density [A/cm²]
    """
    if Ap_cm4 <= 0:
        raise ValueError("Ap must be positive")
    
    J = (apparent_power_VA * 1e4) / (Kf * Ku * Bmax_T * frequency_Hz * Ap_cm4)
    
    return J


def select_flux_density(
    frequency_Hz: float,
    material_type: Literal["ferrite", "silicon_steel", "amorphous", "powder"],
    temp_C: float = 100,
) -> dict:
    """
    Recommend operating flux density based on frequency and material.
    
    At high frequencies, Bmax is LIMITED BY CORE LOSS, not saturation.
    
    Args:
        frequency_Hz: Operating frequency [Hz]
        material_type: Core material type
        temp_C: Operating temperature [°C]
        
    Returns:
        dict with recommended Bmax and reasoning
        
    Reference:
        McLyman, Chapter 4, Table 4-2
    """
    result = {
        "Bmax_T": 0.0,
        "limitation": "",
        "notes": [],
    }
    
    if material_type == "ferrite":
        if frequency_Hz <= 20_000:
            result["Bmax_T"] = 0.30
            result["limitation"] = "saturation_limited"
        elif frequency_Hz <= 100_000:
            result["Bmax_T"] = 0.10
            result["limitation"] = "loss_limited"
        elif frequency_Hz <= 500_000:
            result["Bmax_T"] = 0.05
            result["limitation"] = "loss_limited"
        else:
            result["Bmax_T"] = 0.03
            result["limitation"] = "loss_limited"
        result["notes"].append("Ferrite: loss increases rapidly with B²·f²")
        
    elif material_type == "silicon_steel":
        if frequency_Hz <= 60:
            result["Bmax_T"] = 1.5
            result["limitation"] = "saturation_limited"
        elif frequency_Hz <= 400:
            result["Bmax_T"] = 1.2
            result["limitation"] = "mixed"
        else:
            result["Bmax_T"] = 0.8
            result["limitation"] = "loss_limited"
        result["notes"].append("Silicon steel: not recommended above 1kHz")
        
    elif material_type == "amorphous":
        if frequency_Hz <= 1000:
            result["Bmax_T"] = 1.3
            result["limitation"] = "saturation_limited"
        elif frequency_Hz <= 20_000:
            result["Bmax_T"] = 0.8
            result["limitation"] = "loss_limited"
        else:
            result["Bmax_T"] = 0.4
            result["limitation"] = "loss_limited"
        result["notes"].append("Amorphous: good for 400Hz-20kHz range")
        
    elif material_type == "powder":
        # MPP, Kool Mμ, High Flux
        result["Bmax_T"] = 0.6  # Accounting for DC bias
        result["limitation"] = "dc_bias_limited"
        result["notes"].append("Powder cores: permeability drops with DC bias")
    
    return result
