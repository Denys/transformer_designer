"""
Erickson's Kg and Kgfe Design Methods

Based on "Fundamentals of Power Electronics" by Robert W. Erickson

Kg method: Focuses on minimizing copper loss for given regulation
Kgfe method: Optimizes for minimum total loss (Pfe + Pcu)

These methods are more sophisticated than McLyman's Ap method and
provide better loss-optimized designs for high-frequency applications.
"""

import math
from typing import Tuple, Optional, Dict, Any


def calculate_Kg_erickson(
    rho_cm: float,  # Copper resistivity at operating temp [Ω-cm]
    MLT_cm: float,  # Mean length per turn [cm]
    Ac_cm2: float,  # Core cross-sectional area [cm²]
    Wa_cm2: float,  # Window area [cm²]
    L_cm: float,    # Magnetic path length [cm]
    mu: float = 2000,  # Core relative permeability
) -> float:
    """
    Calculate Erickson's core geometry constant Kg.
    
    Kg characterizes a core's copper loss performance.
    Higher Kg = lower copper loss for given spec.
    
    Args:
        rho_cm: Copper resistivity [Ω-cm] (1.72e-6 at 20°C, 2.3e-6 at 100°C)
        MLT_cm: Mean length per turn [cm]
        Ac_cm2: Core cross-sectional area [cm²]
        Wa_cm2: Window area [cm²]
        L_cm: Magnetic path length [cm]
        mu: Relative permeability
        
    Returns:
        Kg: Core geometry factor [cm⁵]
        
    Reference:
        Erickson, Eq. 14.43
        Kg = (Ac² × Wa) / MLT
    """
    # Erickson's Kg (simplified, regulation-focused)
    Kg = (Ac_cm2 ** 2) * Wa_cm2 / MLT_cm
    
    return Kg


def calculate_required_Kg(
    L_uH: float,           # Required inductance [μH]
    I_max_A: float,        # Maximum current [A]
    B_max_T: float,        # Maximum flux density [T]
    R_max_Ohm: float,      # Maximum winding resistance [Ω]
    Ku: float,             # Window utilization factor
    rho_cm: float = 2.3e-6,  # Copper resistivity at 100°C [Ω-cm]
) -> float:
    """
    Calculate required Kg for an inductor design.
    
    Args:
        L_uH: Required inductance [μH]
        I_max_A: Maximum current [A]
        B_max_T: Maximum flux density [T]
        R_max_Ohm: Maximum allowed DC resistance [Ω]
        Ku: Window utilization factor
        rho_cm: Copper resistivity [Ω-cm]
        
    Returns:
        Required Kg [cm⁵]
        
    Reference:
        Erickson, Chapter 14
    """
    L_H = L_uH * 1e-6
    
    # Required Kg
    Kg_required = (rho_cm * L_H**2 * I_max_A**2) / (B_max_T**2 * R_max_Ohm * Ku)
    
    # Convert to cm⁵
    Kg_required_cm5 = Kg_required * 1e8
    
    return Kg_required_cm5


def calculate_Kgfe_erickson(
    Ac_cm2: float,    # Core cross-sectional area [cm²]
    Wa_cm2: float,    # Window area [cm²]
    MLT_cm: float,    # Mean length per turn [cm]
    lm_cm: float,     # Magnetic path length [cm]
    Ku: float = 0.4,  # Window utilization
) -> float:
    """
    Calculate Erickson's Kgfe core geometry constant for loss optimization.
    
    Kgfe is used for designs that minimize total loss (core + copper).
    
    Args:
        Ac_cm2: Core cross-sectional area [cm²]
        Wa_cm2: Window area [cm²]
        MLT_cm: Mean length per turn [cm]
        lm_cm: Magnetic path length [cm]
        Ku: Window utilization
        
    Returns:
        Kgfe: Core geometry factor for loss optimization [cm⁵] (or other units)
        
    Reference:
        Erickson, Eq. 15.XX
    """
    # Kgfe formula (similar structure to Kg but includes lm)
    # Different formulations exist; this is one common form
    Kgfe = (Wa_cm2 * Ac_cm2**2 * Ku) / (MLT_cm * lm_cm)
    
    return Kgfe


def optimal_Bac_for_minimum_loss(
    frequency_Hz: float,
    Ptot_max_W: float,      # Maximum allowed total loss
    Ac_cm2: float,          # Core area
    Ve_cm3: float,          # Core volume
    Wa_cm2: float,          # Window area
    MLT_cm: float,          # Mean length per turn
    Ku: float,              # Window utilization
    n_turns: int,           # Number of turns
    I_rms_A: float,         # RMS current
    k_steinmetz: float,     # Steinmetz k coefficient
    alpha: float,           # Steinmetz α
    beta: float,            # Steinmetz β
    rho_cm: float = 2.3e-6,  # Copper resistivity [Ω-cm]
) -> Tuple[float, Dict[str, float]]:
    """
    Find optimal Bac that minimizes total loss (Erickson approach).
    
    The optimal condition is when dPtot/dBac = 0, which leads to:
    Pfe = (β/(β+2)) × Ptot
    Pcu = (2/(β+2)) × Ptot
    
    For β ≈ 2.5: Pfe ≈ 0.56×Ptot, Pcu ≈ 0.44×Ptot
    
    Args:
        frequency_Hz: Operating frequency [Hz]
        Various core and winding parameters...
        
    Returns:
        Tuple of (optimal_Bac_T, loss_breakdown_dict)
        
    Reference:
        Erickson, Chapter 15 "Transformer Design"
    """
    f_kHz = frequency_Hz / 1000
    
    # For optimal loss balance: Pfe / Pcu = β / 2
    optimal_ratio = beta / 2
    
    # Wire area available
    Aw_total_cm2 = Ku * Wa_cm2 / n_turns
    
    # Copper loss coefficient (Pcu = Kcu / Bac²)
    # The relationship is that Pcu ∝ 1/Bac² (more flux = fewer turns = less copper loss)
    wire_length_cm = n_turns * MLT_cm
    Rdc_per_Bac2 = rho_cm * wire_length_cm / Aw_total_cm2
    Kcu = I_rms_A**2 * Rdc_per_Bac2
    
    # Core loss coefficient (Pfe = Kfe × Bac^β)
    # Pfe = k × f^α × B^β × Ve / 1000
    Kfe = k_steinmetz * (f_kHz ** alpha) * Ve_cm3 / 1000
    
    # Optimal Bac from d(Pfe + Pcu)/dBac = 0
    # β × Kfe × Bac^(β-1) = 2 × Kcu × Bac^(-3)
    # Bac^(β+2) = 2 × Kcu / (β × Kfe)
    Bac_opt_mT = ((2 * Kcu) / (beta * Kfe)) ** (1 / (beta + 2))
    Bac_opt_T = Bac_opt_mT / 1000
    
    # Calculate losses at optimal point
    Pfe = Kfe * (Bac_opt_mT ** beta)
    Pcu = Kcu / (Bac_opt_mT ** 2)
    Ptot = Pfe + Pcu
    
    return Bac_opt_T, {
        "Pfe_W": Pfe,
        "Pcu_W": Pcu,
        "Ptot_W": Ptot,
        "Pfe_Pcu_ratio": Pfe / Pcu if Pcu > 0 else float('inf'),
        "theoretical_optimal_ratio": optimal_ratio,
    }


def calculate_transformer_Kgfe(
    P_out_W: float,           # Output power [W]
    V_pri_V: float,           # Primary voltage [V]
    V_sec_V: float,           # Secondary voltage [V]
    frequency_Hz: float,      # Operating frequency [Hz]
    eta: float,               # Efficiency target (e.g., 0.98)
    alpha_reg: float,         # Regulation (e.g., 0.02 for 2%)
    Ku: float,                # Window utilization
    Kf: float,                # Waveform coefficient (4.44 sine, 4.0 square)
    Kfe: float,               # Core loss coefficient (material dependent)
    beta: float,              # Steinmetz β exponent
    rho_cm: float = 2.3e-6,   # Copper resistivity [Ω-cm]
) -> float:
    """
    Calculate required Kgfe for minimum-loss transformer design.
    
    This is Erickson's approach to transformer design that minimizes
    total loss while meeting regulation requirements.
    
    Args:
        P_out_W: Output power [W]
        V_pri_V: Primary voltage [V]
        V_sec_V: Secondary voltage [V]
        frequency_Hz: Operating frequency [Hz]
        eta: Target efficiency (decimal, e.g., 0.98)
        alpha_reg: Target regulation (decimal, e.g., 0.02)
        Ku: Window utilization factor
        Kf: Waveform coefficient
        Kfe: Material core loss coefficient
        beta: Steinmetz beta exponent
        rho_cm: Copper resistivity [Ω-cm]
        
    Returns:
        Required Kgfe [cm^x] (units depend on formulation)
        
    Reference:
        Erickson, Chapter 15
    """
    # Total apparent power
    # For transformer: Pt = Pout × (1 + 1/η) approximately
    P_t = P_out_W * (1 + 1/eta)
    
    # Allowable total loss
    P_loss = P_out_W * (1 - eta) / eta
    
    # Core loss should be β/(β+2) of total for optimum
    P_fe_target = P_loss * beta / (beta + 2)
    P_cu_target = P_loss * 2 / (beta + 2)
    
    # Required Kgfe (simplified Erickson formula)
    # Real formula involves more parameters
    
    f_kHz = frequency_Hz / 1000
    
    # Simplified Kgfe requirement
    # Kgfe ≥ (ρ × Pt²) / (Kf² × Ku × f² × ΔBopt² × Pcu)
    # This is a simplified version
    
    Kgfe_required = (rho_cm * P_t**2 * 1e8) / (
        Kf**2 * Ku * frequency_Hz**2 * 0.1**2 * P_cu_target
    )
    
    return Kgfe_required


def design_transformer_erickson(
    P_out_W: float,
    V_pri_V: float,
    V_sec_V: float,
    frequency_Hz: float,
    eta_target: float = 0.98,
    alpha_reg: float = 0.02,
    Ku: float = 0.4,
    Kf: float = 4.0,
    k_steinmetz: float = 3.5,
    alpha_steinmetz: float = 1.46,
    beta_steinmetz: float = 2.75,
) -> Dict[str, Any]:
    """
    Design a transformer using Erickson's minimum-loss approach.
    
    This method finds the optimal flux density that minimizes total loss
    while meeting efficiency and regulation requirements.
    
    Args:
        P_out_W: Output power [W]
        V_pri_V: Primary voltage [V]
        V_sec_V: Secondary voltage [V]
        frequency_Hz: Operating frequency [Hz]
        eta_target: Target efficiency (0.95-0.99)
        alpha_reg: Target regulation (0.01-0.05)
        Ku: Window utilization (0.3-0.5)
        Kf: Waveform coefficient (4.0 for square, 4.44 for sine)
        k_steinmetz: Steinmetz k coefficient
        alpha_steinmetz: Steinmetz α exponent
        beta_steinmetz: Steinmetz β exponent
        
    Returns:
        Dict with design parameters and recommendations
    """
    # Apparent power
    P_t = P_out_W * (1 + 1/eta_target)
    
    # Allowable losses
    P_loss_max = P_out_W * (1 - eta_target) / eta_target
    
    # Optimal loss split for Kgfe method
    # Pfe/Pcu = β/2 at optimum
    P_fe_optimal_fraction = beta_steinmetz / (beta_steinmetz + 2)
    P_cu_optimal_fraction = 2 / (beta_steinmetz + 2)
    
    P_fe_target = P_loss_max * P_fe_optimal_fraction
    P_cu_target = P_loss_max * P_cu_optimal_fraction
    
    # Primary and secondary currents
    I_pri = P_out_W / (V_pri_V * eta_target)
    I_sec = P_out_W / V_sec_V
    
    # Turns ratio
    n = V_sec_V / V_pri_V
    
    # For optimal Bac, we need core volume
    # This is iterative in practice - start with estimate
    
    # Estimate optimal Bac (typically 0.05-0.15 T for ferrite at 100kHz)
    f_kHz = frequency_Hz / 1000
    
    # Initial estimate based on typical ferrite
    # Higher frequency -> lower Bac
    Bac_estimate = 0.3 / math.sqrt(f_kHz / 10)  # ~100mT at 100kHz
    Bac_estimate = max(0.05, min(0.2, Bac_estimate))  # Clamp to reasonable range
    
    # Calculate required Ap
    rho_cm = 2.3e-6  # Copper at 100°C
    J = 400  # A/cm² current density
    
    # Ap from modified formula considering optimal loss
    # Ap = (Pt × 10⁴) / (Kf × Ku × Bac × J × f)
    Ap_cm4 = (P_t * 1e4) / (Kf * Ku * Bac_estimate * J * frequency_Hz)
    
    return {
        "method": "Erickson_Kgfe",
        "apparent_power_VA": P_t,
        "max_loss_W": P_loss_max,
        "optimal_core_loss_W": P_fe_target,
        "optimal_copper_loss_W": P_cu_target,
        "optimal_Pfe_Pcu_ratio": beta_steinmetz / 2,
        "estimated_Bac_T": Bac_estimate,
        "estimated_Ap_cm4": Ap_cm4,
        "primary_current_A": I_pri,
        "secondary_current_A": I_sec,
        "turns_ratio": n,
        "notes": [
            f"For minimum loss with β={beta_steinmetz}: Pfe/Pcu = {beta_steinmetz/2:.2f}",
            f"Target: Pfe = {P_fe_target:.2f}W, Pcu = {P_cu_target:.2f}W",
            "Use this to select a core with Kgfe >= required value",
        ],
    }
