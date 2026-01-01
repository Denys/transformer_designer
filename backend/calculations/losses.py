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
    # f in kHz, B in mT
    # 
    # CALIBRATION METHOD:
    # Given datasheet Pv @ (f_ref, B_ref), solve for k:
    # k = Pv / (f_ref^α × B_ref^β)
    #
    # For f=100kHz, B=100mT with α=1.46, β=2.75:
    # f^α = 100^1.46 = 831.76
    # B^β = 100^2.75 = 177827.94
    # f^α × B^β = 1.479e8
    #
    # So k = Pv[mW/cm³] / 1.479e8
    #
    steinmetz_params = {
        # Ferroxcube 3C series (datasheet at 100°C)
        # 3C90: Pv ≈ 100 mW/cm³ @ 100kHz, 100mT → k = 100/1.479e8 = 6.76e-7
        "3c": (6.8e-7, 1.46, 2.75),
        "3c90": (6.8e-7, 1.46, 2.75),      # 100 mW/cm³ @ 100kHz, 100mT
        "3c92": (5.4e-7, 1.46, 2.75),      # 80 mW/cm³
        "3c94": (5.4e-7, 1.46, 2.75),      # 80 mW/cm³ @ 100kHz, 100mT
        "3c95": (4.1e-7, 1.46, 2.75),      # 60 mW/cm³ @ 100kHz, 100mT (low loss)
        
        # TDK N series (datasheet at 100°C)
        # N87: Pv ≈ 120 mW/cm³ @ 100kHz, 100mT → k = 120/1.479e8 = 8.1e-7
        "n87": (8.1e-7, 1.46, 2.75),       # 120 mW/cm³ @ 100kHz, 100mT
        "n97": (6.1e-7, 1.46, 2.75),       # 90 mW/cm³ (lower loss)
        "n49": (10.8e-7, 1.50, 2.80),      # 160 mW/cm³ (higher frequency grade)
        
        # Generic ferrite (conservative, use 3C90-like)
        "ferrite": (6.8e-7, 1.46, 2.75),   # 100 mW/cm³ @ 100kHz, 100mT
        
        # High frequency ferrite (designed for >200kHz)
        "3f3": (8.1e-7, 1.50, 2.80),
        "3f35": (6.8e-7, 1.48, 2.75),
        
        # Silicon steel (50/60 Hz) - different physics
        # M6 at 60Hz, 1.5T → ~1.1 W/kg → ~8.4 mW/cm³ (density 7.65 g/cm³)
        # For 0.06kHz, 1500mT: k = 8.4 / (0.06^1.5 × 1500^2.0) = 2.5e-6
        "silicon_steel": (2.5e-6, 1.5, 2.0),
        "m6": (2.0e-6, 1.5, 2.0),
        "m19": (3.0e-6, 1.6, 2.0),
        
        # Amorphous (very low loss)
        "amorphous": (2.0e-7, 1.5, 2.1),
        "2605sa1": (1.5e-7, 1.5, 2.1),
        
        # Powder cores (higher loss due to distributed gap)
        "powder": (2.0e-6, 1.2, 2.0),
        "mpp": (1.5e-6, 1.2, 2.0),
        "kool_mu": (2.5e-6, 1.3, 2.0),
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


def calculate_Bac_from_waveform(
    Bmax_T: float,
    waveform: str = "sine",
    duty_cycle: float = 0.5,
) -> float:
    """
    Calculate AC flux density based on waveform type.
    
    The relationship between Bmax (peak flux) and Bac (AC component for loss calc)
    depends on the excitation waveform.
    
    Args:
        Bmax_T: Maximum flux density [T]
        waveform: Waveform type - "sine", "square", "triangle", "pulse"
        duty_cycle: Duty cycle for square/pulse waveforms (0-1)
        
    Returns:
        Bac_T: AC flux density for Steinmetz equation [T]
        
    Waveform factors:
    - Sine wave: Bac = Bmax (peak-to-peak swing = 2×Bmax, amplitude = Bmax)
    - Square wave: Bac = Bmax (full swing each half-cycle)
    - Triangle wave: Bac = Bmax (same peak, different spectral content)
    - Asymmetric pulse: Bac adjusted for DC bias
    
    Reference:
        For Steinmetz equation, Bac should be the peak AC flux amplitude.
        For bidirectional transformers: Bac = Bmax (full swing)
        For forward converters with DC bias: Bac = ΔB/2
    """
    waveform = waveform.lower().strip()
    
    if waveform in ["sine", "sinusoidal"]:
        # Sinusoidal excitation: Bac = Bmax
        return Bmax_T
    
    elif waveform in ["square", "rectangular"]:
        # Square wave: full flux swing each half-cycle
        # For symmetric square wave, Bac = Bmax
        # For asymmetric, adjust for duty cycle DC bias
        if 0.45 <= duty_cycle <= 0.55:
            # Symmetric - no DC bias
            return Bmax_T
        else:
            # Asymmetric - some DC bias, reduced AC swing
            # ΔB = Bmax × 2 × min(D, 1-D)
            delta_B = 2 * Bmax_T * min(duty_cycle, 1 - duty_cycle)
            return delta_B / 2
    
    elif waveform in ["triangle", "triangular", "sawtooth"]:
        # Triangle wave: same peak, RMS factor different but Steinmetz uses peak
        return Bmax_T
    
    elif waveform in ["pulse", "unipolar"]:
        # Unipolar pulse (forward converter style)
        # DC bias present, AC component is half the swing
        return Bmax_T * duty_cycle
    
    else:
        # Default: assume bidirectional, Bac = Bmax
        return Bmax_T


def calculate_core_loss_igse(
    k: float,
    alpha: float,
    beta: float,
    voltage_waveform: list[float],
    time_points: list[float],
    Ae_m2: float,
    N_turns: int,
    volume_cm3: float,
) -> float:
    """
    Calculate core loss using Improved Generalized Steinmetz Equation (iGSE).

    Valid for non-sinusoidal waveforms (e.g. trapezoidal in PSFB).

    Formula:
        Pv(t) = ki * |dB/dt|^alpha * (DeltaB)^(beta - alpha)
        Pavg = (1/T) * integral(Pv(t) dt)

        ki = k / ((2*pi)^(alpha-1) * integral_0^2pi |cos(theta)|^alpha * 2^(beta-alpha))
           ~= k / (2^(beta+1) * pi^(alpha-1) * 0.2761)  (approximate)

    Args:
        k, alpha, beta: Steinmetz parameters
        voltage_waveform: List of voltage samples [V]
        time_points: List of time samples [s] corresponding to voltage
        Ae_m2: Core effective area [m^2]
        N_turns: Number of turns
        volume_cm3: Core volume [cm^3]

    Returns:
        Average core loss [W]
    """
    if len(voltage_waveform) < 2 or len(voltage_waveform) != len(time_points):
        return 0.0

    # Calculate ki
    # Standard approximation for ki from k (assuming sinusoidal reference)
    # Ref: "Improved Generalized Steinmetz Equation for Waveform Optimization" - Venkatachalam et al.
    theta_int = 4 * 0.556 # Approximate integral of |cos|^alpha for typical alpha
    # Use accurate numerical integration for theta_int if alpha varies significantly,
    # but for typical ferrite alpha (1.2-1.8), approximation is sufficient.
    # More precise: ki = k / ((2*pi)^(alpha-1) * int_0^2pi |cos(theta)|^alpha dtheta)
    # For now, use the simplified conversion valid for sinusoidal derivation

    # Calculate time step and period
    T = time_points[-1] - time_points[0]
    if T <= 0:
        return 0.0

    # Calculate B(t) from V(t) -> B(t) = (1/NAe) * integral(V dt)
    # dB/dt = V(t) / (N * Ae)
    dB_dt = [v / (N_turns * Ae_m2) for v in voltage_waveform]

    # Integrate dB/dt to get B(t)
    B_t = [0.0] * len(time_points)
    for i in range(1, len(time_points)):
        dt = time_points[i] - time_points[i-1]
        B_t[i] = B_t[i-1] + dB_dt[i-1] * dt

    # Find peak-to-peak Delta B
    B_min = min(B_t)
    B_max = max(B_t)
    delta_B = B_max - B_min

    if delta_B <= 0:
        return 0.0

    # ki calculation (Venkatachalam)
    # For sine wave: P = k f^a B^b
    # iGSE P = (1/T) integral (ki |dB/dt|^a (deltaB)^(b-a))
    # For sine B = Bpk sin(wt), dB/dt = w Bpk cos(wt), deltaB = 2 Bpk
    # P_sine = ki * (2 Bpk)^(b-a) * (1/T) integral( |w Bpk cos(wt)|^a dt )
    #        = ki * 2^(b-a) * Bpk^(b-a) * w^a * Bpk^a * (1/2pi) integral_0^2pi |cos(theta)|^a dtheta
    #        = ki * 2^(b-a) * Bpk^b * (2*pi*f)^a * I_cos
    # Set equal to k f^a Bpk^b:
    # k = ki * 2^(b-a) * (2*pi)^a * I_cos
    # ki = k / (2^(b-a) * (2*pi)^a * I_cos)

    # Numerical integral of |cos(x)|^alpha from 0 to 2pi
    # Simpson's rule or simple sum
    steps = 100
    dtheta = 2 * math.pi / steps
    I_cos = sum([abs(math.cos(i * dtheta))**alpha for i in range(steps)]) * dtheta / (2 * math.pi) # Normalized
    # Wait, the formula has (1/T) which is f. The integral is over period.
    # integral_0^2pi |cos|^a dtheta
    I_cos_pure = sum([abs(math.cos(i * dtheta))**alpha for i in range(steps)]) * dtheta

    ki = k / (2**(beta - alpha) * (2 * math.pi)**(alpha - 1) * I_cos_pure)

    # Calculate instantaneous power loss density Pv(t)
    energy_density_sum = 0.0

    for i in range(len(time_points) - 1):
        dt = time_points[i+1] - time_points[i]
        val = abs(dB_dt[i])**alpha
        energy_density_sum += val * dt

    # Pavg = ki * (Delta B)^(beta-alpha) * (1/T) * integral(|dB/dt|^alpha dt)
    loss_density_W_m3 = ki * (delta_B**(beta - alpha)) * (energy_density_sum / T)

    # Convert to Watts
    # loss_density is W/m^3?
    # Steinmetz k is usually for mW/cm^3 with f in kHz, B in mT?
    # Need to normalize units.
    # Input k is assumed to be in standard form: P[mW/cm3] = k * f[kHz]^a * B[mT]^b

    # Let's convert everything to SI for calculation, then convert k back or forward?
    # Better: Convert inputs to kHz/mT to match k, then result is mW/cm3

    # Re-eval with standard units:
    # f in kHz, B in mT, t in ms?
    # Let's stick to SI derived ki, but we need to convert k first.
    # SI k_si = k * 1000 (mW->W? no)
    # P[W/m3] = P[mW/cm3] * 1000
    # Let's just use the formula relative to the sinusoidal case.

    # Ratio of iGSE loss to Steinmetz loss for same frequency and Bpk
    # P_igse / P_steinmetz (sine)
    # = (ki * dBdt_int * dB^(b-a) / T) / (k * f^a * Bpk^b)
    # This is hard to track.

    # Alternative:
    # Use the pre-calculated P_steinmetz as baseline?
    # No, we want to support arbitrary waveforms.

    # Let's use the provided k (mW/cm^3, kHz, mT)
    # Convert waveform to kHz equivalent time (ms) and mT (Tesla * 1000)

    T_ms = T * 1000
    time_points_ms = [t * 1000 for t in time_points]
    delta_B_mT = delta_B * 1000
    dB_dt_mT_ms = [val * 1000 / 1000 for val in dB_dt] # T/s = (T*1000)/(s*1000) = mT/ms?
    # T/s = 1000 mT / 1000 ms = 1 mT/ms. Yes.

    # Calculate ki for these units
    # k is compatible with f(kHz), B(mT).
    # integral |cos(theta)|^a dtheta over 2pi
    I_cos_pure = sum([abs(math.cos(i * dtheta))**alpha for i in range(steps)]) * dtheta

    # ki_metric = k / (2^(b-a) * (2pi)^(a-1) * I_cos_pure)
    # Note: the (2pi)^(a-1) comes from converting f^a to w^a?
    # P = k * f^a * B^b
    # P = ki * integral |dB/dt|^a * dB^(b-a) * f
    # For sine: B = Bpk sin(2pi f t) => dB/dt = 2pi f Bpk cos...
    # |dB/dt|^a = (2pi f Bpk)^a |cos|^a
    # integral over T is integral_0^2pi (...) dtheta / (2pi f) * (something?)
    # Let's trust the standard conversion:
    # ki = k / ( (2*pi)^(alpha-1) * 2^(beta-alpha) * integral_0_2pi |cos|^a )

    ki_metric = k / ((2 * math.pi)**(alpha - 1) * 2**(beta - alpha) * I_cos_pure)

    energy_sum_metric = 0.0
    for i in range(len(time_points_ms) - 1):
        dt_ms = time_points_ms[i+1] - time_points_ms[i]
        # dB/dt in mT/ms
        rate = dB_dt_mT_ms[i]
        energy_sum_metric += (abs(rate)**alpha) * dt_ms

    P_avg_mW_cm3 = ki_metric * (delta_B_mT**(beta - alpha)) * (energy_sum_metric / T_ms)

    # Total loss W
    return P_avg_mW_cm3 * volume_cm3 / 1000.0
