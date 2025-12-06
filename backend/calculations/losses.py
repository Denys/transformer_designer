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
        Pv = k × f^α × B^β [mW/cm³]
        Where f in kHz, B in mT
        
    Reference:
        Manufacturer datasheets, McLyman Chapter 4
    """
    # Steinmetz coefficients by material
    # Format: (k, alpha, beta) where Pv = k × f^α × B^β [mW/cm³]
    # IMPORTANT: f in kHz, B in mT (not T!)
    # Values from manufacturer datasheets at 100°C
    steinmetz_params = {
        # Ferroxcube 3C series (100°C, 100kHz reference)
        "3c": (3.2, 1.46, 2.75),           # 3C90/3C92/3C95 family
        "3c90": (4.0, 1.46, 2.75),         # Ferroxcube 3C90
        "3c92": (3.5, 1.46, 2.75),         # Ferroxcube 3C92
        "3c94": (2.8, 1.46, 2.75),         # Ferroxcube 3C94
        "3c95": (2.5, 1.46, 2.75),         # Ferroxcube 3C95 (low loss)
        
        # TDK N series (100°C reference)
        "n87": (7.7, 1.46, 2.75),          # TDK N87
        "n97": (5.0, 1.46, 2.75),          # TDK N97 (lower loss)
        "n49": (10.0, 1.50, 2.80),         # TDK N49 (higher frequency)
        
        # Generic ferrite (use 3C95-like low loss)
        "ferrite": (3.5, 1.46, 2.75),
        
        # High frequency ferrite 
        "3f3": (6.0, 1.50, 2.80),
        "3f35": (5.0, 1.48, 2.75),
        
        # Silicon steel (50/60 Hz reference) - different units
        "silicon_steel": (0.8, 1.5, 2.0),  # f in kHz, B in mT
        "m6": (0.7, 1.5, 2.0),             # M6 grain-oriented
        "m19": (1.0, 1.6, 2.0),            # Non-oriented
        
        # Amorphous
        "amorphous": (0.3, 1.5, 2.1),
        "2605sa1": (0.25, 1.5, 2.1),
        
        # Powder cores
        "powder": (2.0, 1.2, 2.0),
        "mpp": (1.5, 1.2, 2.0),
        "kool_mu": (2.5, 1.3, 2.0),
    }
    
    # Normalize material name
    mat_key = material.lower().strip()
    
    # Get coefficients - try exact match first
    if mat_key in steinmetz_params:
        k, alpha, beta = steinmetz_params[mat_key]
    # Try partial match (e.g., "3C" matches "3c")
    elif any(mat_key.startswith(key) for key in ["3c", "3f"]):
        k, alpha, beta = steinmetz_params["3c"]
    elif mat_key.startswith("n"):
        k, alpha, beta = steinmetz_params["n87"]
    else:
        # Default to generic ferrite
        k, alpha, beta = steinmetz_params["ferrite"]
    
    # Convert units
    f_kHz = frequency_Hz / 1000  # Hz to kHz
    B_mT = Bac_T * 1000  # T to mT
    
    # Core loss density [mW/cm³]
    # Pv = k × f^α × B^β
    Pv_mW_cm3 = k * (f_kHz ** alpha) * (B_mT ** beta)
    
    # Temperature correction (ferrite loss changes with temp)
    # Loss minimum typically around 80-100°C for most ferrites
    if mat_key in steinmetz_params or mat_key.startswith(("3c", "3f", "n")):
        # Coefficients above are for ~100°C
        # Simple correction: +1% per 10°C deviation from 100°C
        temp_deviation = abs(temperature_C - 100)
        temp_factor = 1 + 0.001 * temp_deviation
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
