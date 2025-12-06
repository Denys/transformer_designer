"""
Loss calculations: core loss and copper loss
Based on McLyman's methodology and Steinmetz equation
"""

import math
from typing import Optional, Tuple


def calculate_core_loss_steinmetz(
    volume_cm3: float,
    frequency_Hz: float,
    Bac_T: float,
    material: str = "ferrite",
    temperature_C: float = 100,
) -> Tuple[float, float]:
    """
    Calculate core loss using Steinmetz equation.
    
    Args:
        volume_cm3: Core volume [cm³]
        frequency_Hz: Operating frequency [Hz]
        Bac_T: AC flux density amplitude [T]
        material: Core material type
        temperature_C: Operating temperature [°C]
        
    Returns:
        Tuple of (core_loss_W, loss_density_mW_cm3)
        
    Formula:
        Pcore = k × f^α × Bac^β × Volume [W]
        
    Reference:
        McLyman, Chapter 4
    """
    # Steinmetz coefficients by material
    # Format: (k, alpha, beta) where P = k × f^α × B^β [mW/cm³]
    # f in kHz, B in T
    steinmetz_params = {
        # Ferrite materials (100°C)
        "ferrite": (1.5e-3, 1.3, 2.5),      # Generic ferrite
        "3C95": (1.2e-3, 1.25, 2.4),        # Ferroxcube 3C95
        "N87": (1.1e-3, 1.3, 2.5),          # TDK N87
        "3F3": (2.0e-3, 1.4, 2.6),          # High frequency ferrite
        
        # Silicon steel (60 Hz reference)
        "silicon_steel": (0.01, 1.5, 2.0),  # M6 grain-oriented
        "M6": (0.01, 1.5, 2.0),
        "M19": (0.02, 1.6, 2.0),            # Non-oriented
        
        # Amorphous
        "amorphous": (0.005, 1.5, 2.1),
        "2605SA1": (0.004, 1.5, 2.1),
        
        # Powder cores
        "powder": (0.03, 1.2, 2.0),
        "MPP": (0.02, 1.2, 2.0),
        "Kool_Mu": (0.04, 1.3, 2.0),
    }
    
    # Get coefficients
    if material.lower() in steinmetz_params:
        k, alpha, beta = steinmetz_params[material.lower()]
    elif material.upper() in steinmetz_params:
        k, alpha, beta = steinmetz_params[material.upper()]
    else:
        # Default to generic ferrite
        k, alpha, beta = steinmetz_params["ferrite"]
    
    # Frequency in kHz for Steinmetz
    f_kHz = frequency_Hz / 1000
    
    # Core loss density [mW/cm³]
    Pv_mW_cm3 = k * (f_kHz ** alpha) * (Bac_T ** beta)
    
    # Temperature correction (ferrite loss increases at high temp)
    if "ferrite" in material.lower() or material.upper() in ["3C95", "N87", "3F3"]:
        # Ferrite loss typically doubles from 25°C to 100°C
        temp_factor = 1 + 0.015 * (temperature_C - 25)
        Pv_mW_cm3 *= temp_factor
    
    # Total core loss [W]
    Pcore_W = Pv_mW_cm3 * volume_cm3 / 1000
    
    return (Pcore_W, Pv_mW_cm3)


def calculate_core_loss_datasheet(
    weight_kg: float,
    frequency_Hz: float,
    Bac_T: float,
    loss_data_W_kg: dict,
) -> float:
    """
    Calculate core loss using manufacturer datasheet values.
    
    Args:
        weight_kg: Core weight [kg]
        frequency_Hz: Operating frequency [Hz]
        Bac_T: AC flux density [T]
        loss_data_W_kg: Dict of {(freq_Hz, B_T): loss_W_kg}
        
    Returns:
        Core loss [W]
        
    Note:
        Interpolates from nearest data points if exact match not found.
    """
    # Find closest data point (simplified - real implementation would interpolate)
    closest_key = min(
        loss_data_W_kg.keys(),
        key=lambda k: abs(k[0] - frequency_Hz) + abs(k[1] - Bac_T) * 1000
    )
    
    loss_per_kg = loss_data_W_kg[closest_key]
    return loss_per_kg * weight_kg


def calculate_copper_loss(
    Rdc_ohm: float,
    current_rms_A: float,
    Rac_Rdc_ratio: float = 1.0,
    temperature_C: float = 100,
    reference_temp_C: float = 20,
) -> float:
    """
    Calculate copper (winding) loss.
    
    Args:
        Rdc_ohm: DC resistance at reference temperature [Ω]
        current_rms_A: RMS current [A]
        Rac_Rdc_ratio: AC/DC resistance ratio
        temperature_C: Operating temperature [°C]
        reference_temp_C: Reference temperature for Rdc [°C]
        
    Returns:
        Copper loss [W]
        
    Formula:
        Pcu = I²rms × Rac
        Rac = Rdc × (1 + α×ΔT) × Fr
    """
    # Temperature coefficient of copper
    alpha = 0.00393
    
    # Temperature correction
    Rdc_at_temp = Rdc_ohm * (1 + alpha * (temperature_C - reference_temp_C))
    
    # AC resistance
    Rac = Rdc_at_temp * Rac_Rdc_ratio
    
    # Copper loss
    Pcu = (current_rms_A ** 2) * Rac
    
    return Pcu


def calculate_total_losses(
    core_loss_W: float,
    primary_copper_loss_W: float,
    secondary_copper_loss_W: float,
    additional_losses_W: float = 0,
) -> dict:
    """
    Calculate total transformer losses and loss breakdown.
    
    Args:
        core_loss_W: Core loss [W]
        primary_copper_loss_W: Primary winding copper loss [W]
        secondary_copper_loss_W: Secondary winding copper loss [W]
        additional_losses_W: Other losses (leads, etc.) [W]
        
    Returns:
        dict with loss breakdown and ratios
    """
    total_copper = primary_copper_loss_W + secondary_copper_loss_W
    total_loss = core_loss_W + total_copper + additional_losses_W
    
    # Optimal design has Pfe ≈ Pcu
    Pfe_Pcu_ratio = core_loss_W / total_copper if total_copper > 0 else float('inf')
    
    return {
        "core_loss_W": core_loss_W,
        "primary_copper_loss_W": primary_copper_loss_W,
        "secondary_copper_loss_W": secondary_copper_loss_W,
        "total_copper_loss_W": total_copper,
        "additional_losses_W": additional_losses_W,
        "total_loss_W": total_loss,
        "Pfe_Pcu_ratio": Pfe_Pcu_ratio,
        "loss_balance": "optimal" if 0.5 <= Pfe_Pcu_ratio <= 2.0 else (
            "core_dominated" if Pfe_Pcu_ratio > 2 else "copper_dominated"
        ),
    }


def calculate_efficiency(
    output_power_W: float,
    total_loss_W: float,
) -> float:
    """
    Calculate transformer efficiency.
    
    Args:
        output_power_W: Output power [W]
        total_loss_W: Total losses [W]
        
    Returns:
        Efficiency in percent [%]
    """
    input_power = output_power_W + total_loss_W
    if input_power <= 0:
        return 0.0
    
    efficiency = (output_power_W / input_power) * 100
    return efficiency


def estimate_loss_for_sizing(
    output_power_W: float,
    target_efficiency_percent: float,
) -> float:
    """
    Estimate total losses for initial sizing.
    
    Args:
        output_power_W: Output power [W]
        target_efficiency_percent: Target efficiency [%]
        
    Returns:
        Estimated total loss [W]
    """
    eta = target_efficiency_percent / 100
    input_power = output_power_W / eta
    loss = input_power - output_power_W
    return loss
