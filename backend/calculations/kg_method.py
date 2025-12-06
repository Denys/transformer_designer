"""
Core Geometry (Kg) Method for regulation-critical transformer design
Based on McLyman's methodology

Kg method is preferred when voltage regulation is a primary concern.
"""

import math
from typing import Literal


def calculate_electrical_coefficient(
    frequency_Hz: float,
    Bmax_T: float,
    Kf: float = 4.44,
) -> float:
    """
    Calculate electrical coefficient Ke for Kg method.
    
    Args:
        frequency_Hz: Operating frequency [Hz]
        Bmax_T: Maximum flux density [T]
        Kf: Waveform coefficient (4.44 for sine, 4.0 for square)
        
    Returns:
        Ke: Electrical coefficient
        
    Formula:
        Ke = 0.145 × Kf² × f² × Bm² × 10⁻⁴
        
    Reference:
        McLyman, Eq. 5-11
    """
    if any(v <= 0 for v in [frequency_Hz, Bmax_T]):
        raise ValueError("Frequency and Bmax must be positive")
    
    Ke = 0.145 * (Kf ** 2) * (frequency_Hz ** 2) * (Bmax_T ** 2) * 1e-4
    
    return Ke


def calculate_core_geometry(
    apparent_power_VA: float,
    regulation_percent: float,
    Ke: float,
) -> float:
    """
    Calculate required Core Geometry (Kg) for transformer.
    
    Args:
        apparent_power_VA: Apparent power Pt [VA]
        regulation_percent: Target voltage regulation α [%]
        Ke: Electrical coefficient from calculate_electrical_coefficient()
        
    Returns:
        Kg: Required core geometry [cm⁵]
        
    Formula:
        Kg = (Pt × 10⁴) / (2 × Ke × α)
        
    Reference:
        McLyman, Eq. 5-12
    """
    if any(v <= 0 for v in [apparent_power_VA, regulation_percent, Ke]):
        raise ValueError("All input parameters must be positive")
    
    # α is regulation in percent (not decimal)
    Kg = (apparent_power_VA * 1e4) / (2 * Ke * regulation_percent)
    
    return Kg


def kg_to_ap(Kg_cm5: float, core_type: str = "EE") -> float:
    """
    Convert Kg to equivalent Ap using empirical relationship.
    
    Args:
        Kg_cm5: Core geometry [cm⁵]
        core_type: Core geometry type (EE, ETD, PQ, pot, etc.)
        
    Returns:
        Ap: Equivalent area product [cm⁴]
        
    Formula:
        Ap = Kp × Kg^0.8
        
    Reference:
        McLyman, Table 5-3
        Kp varies by core type:
        - EE cores: Kp ≈ 48
        - Pot cores: Kp ≈ 25
        - Toroid: Kp ≈ 30
    """
    Kp_values = {
        "EE": 48,
        "ETD": 48,
        "PQ": 45,
        "RM": 40,
        "pot": 25,
        "toroid": 30,
        "EI": 50,
        "UI": 55,
    }
    
    Kp = Kp_values.get(core_type.upper(), 48)
    
    Ap = Kp * (Kg_cm5 ** 0.8)
    
    return Ap


def calculate_regulation(
    Rdc_primary_mOhm: float,
    Rdc_secondary_mOhm: float,
    primary_current_A: float,
    secondary_current_A: float,
    output_voltage_V: float,
) -> float:
    """
    Calculate voltage regulation from winding resistances.
    
    Args:
        Rdc_primary_mOhm: Primary DC resistance [mΩ]
        Rdc_secondary_mOhm: Secondary DC resistance [mΩ]
        primary_current_A: Primary RMS current [A]
        secondary_current_A: Secondary RMS current [A]
        output_voltage_V: Nominal output voltage [V]
        
    Returns:
        Regulation in percent [%]
        
    Formula:
        ΔV = Ip²×Rp + Is²×Rs (power loss approach)
        α = (ΔV / Vo) × 100
    """
    # Convert mΩ to Ω
    Rp = Rdc_primary_mOhm / 1000
    Rs = Rdc_secondary_mOhm / 1000
    
    # Voltage drops
    voltage_drop_primary = primary_current_A * Rp
    voltage_drop_secondary = secondary_current_A * Rs
    
    # Approximate regulation (simplified)
    total_drop = voltage_drop_primary + voltage_drop_secondary
    regulation_percent = (total_drop / output_voltage_V) * 100
    
    return regulation_percent


def select_design_method(
    regulation_target_percent: float,
    output_power_W: float,
    frequency_Hz: float = 50000,  # Add frequency parameter
) -> Literal["Ap", "Kg"]:
    """
    Recommend design method based on requirements.
    
    Args:
        regulation_target_percent: Target regulation [%]
        output_power_W: Output power [W]
        frequency_Hz: Operating frequency [Hz]
        
    Returns:
        Recommended method: "Ap" or "Kg"
        
    Guidelines:
        - Ap method is preferred for high-frequency SMPS (>1kHz)
        - Kg method for low-frequency, regulation-critical designs
        - The Kg->Ap conversion is only reliable for 50/60Hz designs
    """
    # For high-frequency SMPS, always use Ap method
    # The kg_to_ap conversion is unreliable at high frequencies
    if frequency_Hz > 1000:
        return "Ap"
    
    # For low-frequency (50/60Hz), use Kg if regulation is critical
    if regulation_target_percent < 3:
        return "Kg"
    else:
        return "Ap"

