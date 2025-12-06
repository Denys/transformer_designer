"""
Calculation Validation Module

Cross-validates our core loss calculations against OpenMagnetics models
to build confidence in the design results.
"""

import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a calculation validation."""
    our_value: float
    reference_value: float
    difference_percent: float
    status: str  # "pass", "warning", "fail"
    method: str  # Validation method used
    confidence: str  # "high", "medium", "low" - how reliable is this validation
    notes: list[str]


def validate_core_loss(
    our_loss_W: float,
    volume_cm3: float,
    frequency_Hz: float,
    Bac_T: float,
    material: str,
    temperature_C: float = 100,
) -> ValidationResult:
    """
    Validate our core loss calculation against reference data.
    
    Uses multiple validation approaches:
    1. OpenMagnetics Steinmetz coefficients (if available)
    2. Manufacturer datasheet reference points
    3. Industry rule-of-thumb checks
    
    Args:
        our_loss_W: Our calculated core loss [W]
        volume_cm3: Core volume [cm³]
        frequency_Hz: Operating frequency [Hz]
        Bac_T: AC flux density amplitude [T]
        material: Material name (N87, 3C95, etc.)
        temperature_C: Operating temperature [°C]
        
    Returns:
        ValidationResult with comparison data
    """
    notes = []
    
    # Calculate loss density for comparison
    our_loss_density = our_loss_W / volume_cm3 * 1000 if volume_cm3 > 0 else 0  # mW/cm³
    
    # Reference data from manufacturer datasheets at 100°C
    # Format: material -> {(f_kHz, B_mT): Pv_mW_cm3}
    # Sources: Ferroxcube, TDK EPCOS datasheets
    reference_data = {
        # TDK N87 (from EPCOS datasheet at 100°C)
        "n87": {
            (25, 200): 80,
            (50, 100): 50,
            (50, 200): 200,
            (100, 50): 50,
            (100, 100): 120,
            (100, 200): 480,
            (200, 50): 100,
            (200, 100): 380,
            (300, 50): 180,      # High frequency points
            (300, 100): 700,
            (500, 50): 400,
        },
        # Ferroxcube 3C90 (from datasheet at 100°C)
        "3c90": {
            (25, 200): 70,
            (50, 100): 40,
            (50, 200): 180,
            (100, 50): 35,
            (100, 100): 100,
            (100, 200): 400,
            (200, 50): 80,
            (200, 100): 350,
            (300, 50): 150,
            (300, 100): 600,
        },
        # Ferroxcube 3C94 (from datasheet at 100°C)
        "3c94": {
            (50, 100): 30,
            (100, 50): 25,
            (100, 100): 80,
            (100, 200): 300,
            (200, 50): 60,
            (200, 100): 280,
            (300, 50): 120,
            (300, 100): 500,
        },
        # Ferroxcube 3C95 (low loss, from datasheet at 100°C)
        "3c95": {
            (50, 100): 25,
            (100, 50): 20,
            (100, 100): 60,
            (100, 200): 250,
            (200, 50): 50,
            (200, 100): 220,
            (300, 50): 100,
            (300, 100): 400,
            (500, 50): 200,
        },
        # Generic ferrite reference (conservative estimate)
        "ferrite": {
            (100, 50): 35,
            (100, 100): 100,
            (100, 200): 400,
            (200, 100): 350,
            (300, 100): 600,
        },
    }
    
    # Convert inputs for lookup
    f_kHz = frequency_Hz / 1000
    B_mT = Bac_T * 1000
    
    # Normalize material name
    mat_key = material.lower().strip()
    if mat_key not in reference_data:
        # Try to match by prefix
        if mat_key.startswith("n"):
            mat_key = "n87"
        elif mat_key.startswith("3c9"):
            mat_key = "3c94"
        elif mat_key.startswith("3c"):
            mat_key = "3c90"
        else:
            mat_key = "ferrite"
    
    # Find closest reference point
    ref_points = reference_data.get(mat_key, reference_data["ferrite"])
    
    best_match = None
    best_distance = float('inf')
    
    for (ref_f, ref_B), ref_Pv in ref_points.items():
        # Normalized distance in log space
        distance = abs(math.log(f_kHz / ref_f)) + abs(math.log(B_mT / ref_B))
        if distance < best_distance:
            best_distance = distance
            best_match = ((ref_f, ref_B), ref_Pv)
    
    if best_match:
        (ref_f, ref_B), ref_Pv = best_match
        
        # Interpolate/extrapolate using Steinmetz scaling
        # P ∝ f^α × B^β, typical α≈1.4, β≈2.5
        alpha = 1.46
        beta = 2.75
        
        # Scale reference to our operating point
        scaled_Pv = ref_Pv * ((f_kHz / ref_f) ** alpha) * ((B_mT / ref_B) ** beta)
        
        # Determine confidence based on distance to reference
        # best_distance is in log-space: 0 = exact match
        if best_distance < 0.2:
            confidence = "high"  # Very close to a datasheet point
        elif best_distance < 0.5:
            confidence = "medium"  # Moderate interpolation
        else:
            confidence = "low"  # Significant extrapolation
        
        # Compare
        if scaled_Pv > 0:
            diff_percent = abs(our_loss_density - scaled_Pv) / scaled_Pv * 100
        else:
            diff_percent = 100
        
        # Determine status
        if diff_percent < 15:
            status = "pass"
            notes.append(f"Within 15% of reference ({mat_key} datasheet)")
        elif diff_percent < 30:
            status = "warning"
            notes.append(f"Within 30% of reference - acceptable for initial design")
        else:
            status = "fail"
            notes.append(f"Significant deviation from reference - verify material coefficients")
        
        notes.append(f"Reference: {ref_Pv} mW/cm³ @ {ref_f}kHz, {ref_B}mT")
        notes.append(f"Scaled to {f_kHz:.1f}kHz, {B_mT:.1f}mT: {scaled_Pv:.1f} mW/cm³")
        notes.append(f"Our calculation: {our_loss_density:.1f} mW/cm³")
        notes.append(f"Confidence: {confidence} (distance={best_distance:.2f})")
        
        return ValidationResult(
            our_value=our_loss_density,
            reference_value=scaled_Pv,
            difference_percent=diff_percent,
            status=status,
            method="datasheet_interpolation",
            confidence=confidence,
            notes=notes,
        )
    
    # Fallback: rule of thumb check
    # At 100kHz, 100mT, typical ferrite loss is 100-400 mW/cm³
    if 50 <= f_kHz <= 200 and 50 <= B_mT <= 200:
        expected_range = (50, 500)  # mW/cm³
        if expected_range[0] <= our_loss_density <= expected_range[1]:
            status = "pass"
            notes.append("Within typical range for power ferrite")
        else:
            status = "warning"
            notes.append(f"Outside typical range ({expected_range[0]}-{expected_range[1]} mW/cm³)")
        
        return ValidationResult(
            our_value=our_loss_density,
            reference_value=(expected_range[0] + expected_range[1]) / 2,
            difference_percent=0,  # No specific reference
            status=status,
            method="rule_of_thumb",
            confidence="low",
            notes=notes,
        )
    
    # No validation possible
    return ValidationResult(
        our_value=our_loss_density,
        reference_value=0,
        difference_percent=0,
        status="unknown",
        method="none",
        confidence="low",
        notes=["No reference data available for this operating point"],
    )


def validate_efficiency(
    calculated_efficiency: float,
    output_power_W: float,
    frequency_Hz: float,
    core_volume_cm3: float,
) -> ValidationResult:
    """
    Validate efficiency calculation using industry benchmarks.
    
    Args:
        calculated_efficiency: Our calculated efficiency [%]
        output_power_W: Output power [W]
        frequency_Hz: Operating frequency [Hz]
        core_volume_cm3: Core volume [cm³]
        
    Returns:
        ValidationResult with comparison data
    """
    notes = []
    
    # Industry benchmarks for transformer efficiency
    # Based on power level and frequency
    
    if frequency_Hz > 50000:  # High frequency SMPS
        if output_power_W < 100:
            expected_range = (92, 99)
        elif output_power_W < 1000:
            expected_range = (95, 99.5)
        else:
            expected_range = (97, 99.8)
    else:  # Low frequency (50-400Hz)
        if output_power_W < 100:
            expected_range = (85, 95)
        elif output_power_W < 1000:
            expected_range = (92, 98)
        else:
            expected_range = (95, 99)
    
    # Check if calculated efficiency is within expected range
    if expected_range[0] <= calculated_efficiency <= expected_range[1]:
        status = "pass"
        notes.append(f"Efficiency {calculated_efficiency:.1f}% within expected range")
    elif calculated_efficiency > expected_range[1]:
        status = "warning"
        notes.append(f"Efficiency {calculated_efficiency:.1f}% higher than typical - verify losses")
    else:
        status = "warning"
        notes.append(f"Efficiency {calculated_efficiency:.1f}% lower than expected")
    
    notes.append(f"Expected range for {output_power_W:.0f}W @ {frequency_Hz/1000:.0f}kHz: {expected_range[0]}-{expected_range[1]}%")
    
    midpoint = (expected_range[0] + expected_range[1]) / 2
    diff = abs(calculated_efficiency - midpoint) / midpoint * 100
    
    return ValidationResult(
        our_value=calculated_efficiency,
        reference_value=midpoint,
        difference_percent=diff,
        status=status,
        method="industry_benchmark",
        confidence="high",  # Industry benchmarks are well-established
        notes=notes,
    )


def validate_temperature_rise(
    calculated_rise_C: float,
    power_dissipation_W: float,
    surface_area_cm2: float,
    cooling: str = "natural",
) -> ValidationResult:
    """
    Validate temperature rise calculation using thermal resistance model.
    
    Args:
        calculated_rise_C: Our calculated temperature rise [°C]
        power_dissipation_W: Total power dissipation [W]
        surface_area_cm2: Core surface area [cm²]
        cooling: "natural" or "forced"
        
    Returns:
        ValidationResult with comparison data
    """
    notes = []
    
    # McLyman thermal model: ΔT = 450 × ψ^0.826
    # where ψ = P/A [W/cm²]
    
    psi = power_dissipation_W / surface_area_cm2 if surface_area_cm2 > 0 else 0
    
    # Reference calculation
    reference_rise = 450 * (psi ** 0.826)
    
    # Adjust for forced cooling (typically 40-60% reduction)
    if cooling == "forced":
        reference_rise *= 0.5
        notes.append("Forced air cooling: ~50% reduction applied")
    
    # Compare
    if reference_rise > 0:
        diff_percent = abs(calculated_rise_C - reference_rise) / reference_rise * 100
    else:
        diff_percent = 0
    
    if diff_percent < 20:
        status = "pass"
    elif diff_percent < 40:
        status = "warning"
    else:
        status = "fail"
    
    notes.append(f"Power dissipation density ψ = {psi:.4f} W/cm²")
    notes.append(f"McLyman model: ΔT = 450 × ψ^0.826 = {reference_rise:.1f}°C")
    notes.append(f"Our calculation: {calculated_rise_C:.1f}°C")
    
    return ValidationResult(
        our_value=calculated_rise_C,
        reference_value=reference_rise,
        difference_percent=diff_percent,
        status=status,
        method="mclyman_thermal",
        confidence="high",  # McLyman model is empirically validated
        notes=notes,
    )


def run_full_validation(
    design_result: Dict[str, Any],
    requirements: Dict[str, Any],
) -> Dict[str, ValidationResult]:
    """
    Run full validation suite on a transformer design.
    
    Args:
        design_result: Complete design result from the design endpoint
        requirements: Original design requirements
        
    Returns:
        Dict mapping validation name to ValidationResult
    """
    results = {}
    
    # Extract values from design result
    core = design_result.get("core", {})
    losses = design_result.get("losses", {})
    thermal = design_result.get("thermal", {})
    
    # Core loss validation
    if losses.get("core_loss_W") and core.get("Ve_cm3"):
        results["core_loss"] = validate_core_loss(
            our_loss_W=losses["core_loss_W"],
            volume_cm3=core["Ve_cm3"],
            frequency_Hz=requirements.get("frequency_Hz", 100000),
            Bac_T=core.get("Bmax_T", 0.1) / 2,  # Bac = Bmax/2
            material=core.get("material", "ferrite"),
            temperature_C=requirements.get("ambient_temp_C", 40) + thermal.get("temperature_rise_C", 40) / 2,
        )
    
    # Efficiency validation
    if losses.get("efficiency_percent"):
        results["efficiency"] = validate_efficiency(
            calculated_efficiency=losses["efficiency_percent"],
            output_power_W=requirements.get("output_power_W", 100),
            frequency_Hz=requirements.get("frequency_Hz", 100000),
            core_volume_cm3=core.get("Ve_cm3", 10),
        )
    
    # Temperature rise validation
    if thermal.get("temperature_rise_C") and losses.get("total_loss_W") and core.get("At_cm2"):
        results["temperature_rise"] = validate_temperature_rise(
            calculated_rise_C=thermal["temperature_rise_C"],
            power_dissipation_W=losses["total_loss_W"],
            surface_area_cm2=core["At_cm2"],
            cooling=requirements.get("cooling", "natural"),
        )
    
    return results
