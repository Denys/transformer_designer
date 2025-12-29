"""
Thermal analysis calculations
Based on McLyman's thermal model
"""

import math
from typing import Literal, Tuple


def calculate_surface_area(
    Ap_cm4: float,
    core_type: str = "EE",
) -> float:
    """
    Estimate core surface area from area product.
    
    Args:
        Ap_cm4: Area product [cm⁴]
        core_type: Core geometry type
        
    Returns:
        Surface area At [cm²]
        
    Formula:
        At = Ks × Ap^0.5
        
    Where Ks depends on core type (McLyman Table 5-4):
        - EE cores: Ks ≈ 39
        - ETD cores: Ks ≈ 41
        - PQ cores: Ks ≈ 35
        - Pot cores: Ks ≈ 32
        - Toroid: Ks ≈ 48
        
    Reference:
        McLyman, Eq. 5-17
    """
    Ks_values = {
        "EE": 39,
        "ETD": 41,
        "PQ": 35,
        "RM": 33,
        "pot": 32,
        "toroid": 48,
        "EI": 42,
        "UI": 45,
    }
    
    Ks = Ks_values.get(core_type.upper(), 39)
    
    At = Ks * math.sqrt(Ap_cm4)
    
    return At


def calculate_power_dissipation_density(
    total_loss_W: float,
    surface_area_cm2: float,
) -> float:
    """
    Calculate power dissipation density (psi).
    
    Args:
        total_loss_W: Total power loss [W]
        surface_area_cm2: Surface area for cooling [cm²]
        
    Returns:
        Power dissipation density ψ [W/cm²]
    """
    if surface_area_cm2 <= 0:
        raise ValueError("Surface area must be positive")
    
    psi = total_loss_W / surface_area_cm2
    return psi


def calculate_temperature_rise(
    psi_W_cm2: float,
    cooling: Literal["natural", "forced"] = "natural",
) -> float:
    """
    Calculate temperature rise from dissipation density.
    
    Args:
        psi_W_cm2: Power dissipation density [W/cm²]
        cooling: Cooling method
        
    Returns:
        Temperature rise Tr [°C]
        
    Formula (natural convection):
        Tr = 450 × ψ^0.826
        
    Reference:
        McLyman, Eq. 5-18
    """
    if psi_W_cm2 < 0:
        raise ValueError("Dissipation density cannot be negative")
    
    if psi_W_cm2 == 0:
        return 0.0
    
    # Natural convection
    Tr = 450 * (psi_W_cm2 ** 0.826)
    
    # Forced air cooling reduces temperature rise
    if cooling == "forced":
        Tr *= 0.5  # Rough approximation: forced air halves temp rise
    
    return Tr


def calculate_thermal_resistance(
    surface_area_cm2: float,
    cooling: Literal["natural", "forced"] = "natural",
) -> float:
    """
    Calculate thermal resistance to ambient.
    
    Args:
        surface_area_cm2: Surface area [cm²]
        cooling: Cooling method
        
    Returns:
        Thermal resistance Rth [°C/W]
    """
    # Heat transfer coefficient [W/(cm²·°C)]
    if cooling == "natural":
        h = 0.001  # ~10 W/(m²·°C)
    else:
        h = 0.003  # ~30 W/(m²·°C) with forced air
    
    Rth = 1 / (h * surface_area_cm2)
    return Rth


def thermal_analysis(
    total_loss_W: float,
    surface_area_cm2: float,
    ambient_temp_C: float,
    max_temp_rise_C: float,
    cooling: Literal["natural", "forced"] = "natural",
    material_max_temp_C: float = 120,
) -> dict:
    """
    Complete thermal analysis.
    
    Args:
        total_loss_W: Total power dissipation [W]
        surface_area_cm2: Surface area [cm²]
        ambient_temp_C: Ambient temperature [°C]
        max_temp_rise_C: Target maximum temperature rise [°C]
        cooling: Cooling method
        material_max_temp_C: Maximum material temperature [°C]
        
    Returns:
        dict with thermal analysis results
    """
    psi = calculate_power_dissipation_density(total_loss_W, surface_area_cm2)
    Tr = calculate_temperature_rise(psi, cooling)
    hotspot = ambient_temp_C + Tr
    
    # Margin calculations
    margin_to_target = max_temp_rise_C - Tr
    margin_to_material = material_max_temp_C - hotspot
    
    # Status determination
    if Tr > max_temp_rise_C or hotspot > material_max_temp_C:
        status = "error"
    elif margin_to_target < 10 or margin_to_material < 10:
        status = "warning"
    else:
        status = "ok"
    
    # Recommendations
    recommendations = []
    if status == "error":
        if cooling == "natural":
            recommendations.append("Consider forced air cooling")
        recommendations.append("Increase core size to reduce losses")
        recommendations.append("Reduce current density to lower copper loss")
        recommendations.append("Reduce Bmax to lower core loss")
    elif status == "warning":
        recommendations.append("Design is marginal - consider adding thermal margin")
    
    return {
        "power_dissipation_density_W_cm2": psi,
        "temperature_rise_C": Tr,
        "hotspot_temp_C": hotspot,
        "margin_to_target_C": margin_to_target,
        "margin_to_material_C": margin_to_material,
        "status": status,
        "cooling_recommendation": "adequate" if status == "ok" else (
            "forced air recommended" if cooling == "natural" else "heatsink or liquid cooling required"
        ),
        "recommendations": recommendations,
    }


def max_dissipation_for_temp_rise(
    surface_area_cm2: float,
    target_temp_rise_C: float,
    cooling: Literal["natural", "forced"] = "natural",
) -> float:
    """
    Calculate maximum allowable power dissipation for target temperature rise.
    
    Args:
        surface_area_cm2: Surface area [cm²]
        target_temp_rise_C: Target temperature rise [°C]
        cooling: Cooling method
        
    Returns:
        Maximum power dissipation [W]
    """
    # Invert: Tr = 450 × ψ^0.826
    # ψ = (Tr / 450)^(1/0.826)
    psi_max = (target_temp_rise_C / 450) ** (1 / 0.826)
    
    if cooling == "forced":
        psi_max *= 2  # Forced air allows ~2x dissipation
    
    P_max = psi_max * surface_area_cm2
    
    return P_max


# Reference table for typical dissipation limits
DISSIPATION_TARGETS = {
    # (temp_rise_C, cooling) -> psi_W_cm2
    (25, "natural"): 0.03,
    (40, "natural"): 0.05,
    (50, "natural"): 0.07,
    (65, "natural"): 0.10,
    (40, "forced"): 0.10,
    (65, "forced"): 0.15,
}


def thermal_mass_estimate(
    core_weight_kg: float,
    copper_weight_kg: float,
    specific_heat_core: float = 450,    # J/kg·°C (Si-steel)
    specific_heat_copper: float = 385   # J/kg·°C
) -> float:
    """
    Estimate thermal mass for transient calculations.

    Args:
        core_weight_kg: Core weight [kg]
        copper_weight_kg: Copper weight [kg]
        specific_heat_core: Specific heat of core [J/kg·°C]
        specific_heat_copper: Specific heat of copper [J/kg·°C]

    Returns:
        Thermal mass [J/°C]
    """
    c_th = (core_weight_kg * specific_heat_core) + (copper_weight_kg * specific_heat_copper)
    return c_th


def thermal_pulsed_operation(
    peak_power: float,            # W (instantaneous)
    average_power: float,         # W (time-averaged)
    pulse_width: float,           # seconds
    duty_cycle: float,            # fraction
    thermal_mass: float,          # J/°C (copper + core)
    thermal_resistance: float     # °C/W (to ambient)
) -> dict:
    """
    Calculate temperature for pulsed operation.

    Two thermal time constants:
    1. τ_pulse: heating during pulse (thermal mass limited)
    2. τ_avg: steady-state (thermal resistance limited)

    Args:
        peak_power: Peak power dissipation [W]
        average_power: Average power dissipation [W]
        pulse_width: Pulse width [s]
        duty_cycle: Duty cycle (0-1)
        thermal_mass: Thermal mass [J/°C]
        thermal_resistance: Thermal resistance [°C/W]

    Returns:
        Dictionary with temperature rise estimates
    """
    # Steady state rise based on average power
    temp_rise_average = average_power * thermal_resistance

    # Transient rise during a single pulse (adiabatic assumption for short pulse)
    # Energy = P_peak * t_pulse
    # dQ = C_th * dT -> dT = Energy / C_th
    energy_per_pulse = peak_power * pulse_width
    temp_rise_pulse = energy_per_pulse / thermal_mass if thermal_mass > 0 else 0

    # Peak temperature rise (Average + Ripple)
    # Actually, the ripple is superimposed on the average.
    # The peak is roughly Avg + dT_pulse/2 (sawtooth approx)
    # But if duty is very low, it cools down significantly between pulses.

    temp_peak = temp_rise_average + temp_rise_pulse

    return {
        "temp_rise_average_C": temp_rise_average,
        "temp_rise_pulse_C": temp_rise_pulse,
        "temp_peak_rise_C": temp_peak,
        "energy_per_pulse_J": energy_per_pulse,
        "thermal_time_constant_s": thermal_mass * thermal_resistance if thermal_resistance > 0 else 0
    }


def natural_convection_rating(
    surface_area_cm2: float,
    max_temp_rise: float,
    ambient_temp: float = 40
) -> float:
    """
    Calculate power dissipation capability with natural convection.

    Args:
        surface_area_cm2: Surface area [cm²]
        max_temp_rise: Maximum temperature rise [°C]
        ambient_temp: Ambient temperature [°C]

    Returns:
        Max power capability [W]
    """
    # Based on McLyman: Tr = 450 * psi^0.826
    # psi = (Tr/450)^(1/0.826)

    psi = (max_temp_rise / 450) ** (1 / 0.826)

    return psi * surface_area_cm2
