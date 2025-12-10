"""
Cross-validation module for transformer design calculations.

Compares our McLyman/Erickson calculations against:
- OpenMagnetics PyMKF models
- Reference textbook examples
- Datasheet specifications

This enables confidence scoring and helps identify calculation errors.
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from calculations.losses import calculate_Bac_from_waveform

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """Confidence level for validation."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    parameter: str
    our_value: float
    reference_value: float
    unit: str
    difference_percent: float
    status: ValidationStatus
    confidence: ConfidenceLevel
    source: str
    notes: str = ""


@dataclass
class CrossValidationReport:
    """Complete cross-validation report."""
    design_method: str
    validations: List[ValidationResult] = field(default_factory=list)
    overall_status: ValidationStatus = ValidationStatus.UNKNOWN
    overall_confidence: float = 0.0
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)


class TransformerValidator:
    """
    Cross-validation engine for transformer designs.
    
    Compares calculated values against:
    1. OpenMagnetics models (core loss, Steinmetz coefficients)
    2. Theoretical bounds (Faraday's law, thermal limits)
    3. Reference designs from literature
    """
    
    # Tolerance thresholds for validation [%]
    PASS_THRESHOLD = 5.0      # Within 5% = pass
    WARNING_THRESHOLD = 15.0  # Within 15% = warning, >15% = fail
    
    def __init__(self, openmagnetics_db=None):
        """
        Initialize validator.
        
        Args:
            openmagnetics_db: OpenMagneticsDB instance for cross-checking
        """
        self._om_db = openmagnetics_db
    
    def validate_transformer_design(
        self,
        design_result: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> CrossValidationReport:
        """
        Perform comprehensive cross-validation of a transformer design.
        
        Args:
            design_result: Complete design result dictionary
            requirements: Original design requirements
            
        Returns:
            CrossValidationReport with all validation results
        """
        report = CrossValidationReport(
            design_method=design_result.get('design_method', 'unknown')
        )
        
        # 1. Validate turns calculation against Faraday's law
        turns_result = self._validate_turns(design_result, requirements)
        if turns_result:
            report.validations.append(turns_result)
        
        # 2. Validate core loss against Steinmetz equation
        loss_result = self._validate_core_loss(design_result, requirements)
        if loss_result:
            report.validations.append(loss_result)
        
        # 3. Validate flux density bounds
        flux_result = self._validate_flux_density(design_result, requirements)
        if flux_result:
            report.validations.append(flux_result)
        
        # 4. Validate thermal estimate
        thermal_result = self._validate_thermal(design_result)
        if thermal_result:
            report.validations.append(thermal_result)
        
        # 5. Validate efficiency bounds
        efficiency_result = self._validate_efficiency(design_result, requirements)
        if efficiency_result:
            report.validations.append(efficiency_result)
        
        # 6. Validate window utilization
        ku_result = self._validate_window_utilization(design_result)
        if ku_result:
            report.validations.append(ku_result)
        
        # 7. Cross-check with OpenMagnetics if available
        if self._om_db and self._om_db.is_available:
            om_results = self._validate_against_openmagnetics(design_result, requirements)
            report.validations.extend(om_results)
        
        # Calculate overall status and confidence
        self._calculate_overall_status(report)
        
        return report
    
    def _validate_turns(
        self,
        design: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Validate primary turns using Faraday's law.
        
        N = V / (4 * Kf * f * Bmax * Ae)
        where Kf = 4.0 for square wave, 4.44 for sinusoidal
        """
        try:
            winding = design.get('winding', {})
            core = design.get('core', {})
            
            Np_calc = winding.get('primary_turns', 0)
            if Np_calc == 0:
                return None
            
            Vp = requirements.get('primary_voltage_V', 0)
            freq = requirements.get('frequency_Hz', 0)
            waveform = requirements.get('waveform', 'sinusoidal')
            Bmax = core.get('Bmax_T', 0.25)
            Ae_cm2 = core.get('Ae_cm2', 0)
            Ae_m2 = Ae_cm2 * 1e-4
            
            if freq <= 0 or Ae_m2 <= 0:
                return None
            
            # Waveform coefficient
            Kf = 4.0 if waveform == 'square' else 4.44
            
            # Faraday's law calculation
            Np_ref = Vp / (Kf * freq * Bmax * Ae_m2)
            
            diff_pct = abs(Np_calc - Np_ref) / Np_ref * 100 if Np_ref > 0 else 0
            
            status = self._get_status(diff_pct)
            
            return ValidationResult(
                parameter="primary_turns",
                our_value=Np_calc,
                reference_value=round(Np_ref, 1),
                unit="turns",
                difference_percent=round(diff_pct, 2),
                status=status,
                confidence=ConfidenceLevel.HIGH,
                source="Faraday's Law",
                notes=f"Kf={Kf} for {waveform} waveform"
            )
            
        except Exception as e:
            logger.warning(f"Turns validation error: {e}")
            return None
    
    def _validate_core_loss(
        self,
        design: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Validate core loss using Steinmetz equation.
        
        Pcore = k * f^α * B^β * Ve
        """
        try:
            losses = design.get('losses', {})
            core = design.get('core', {})
            
            Pcore_calc = losses.get('core_loss_W', 0)
            if Pcore_calc == 0:
                return None
            
            # Get Steinmetz parameters
            material = core.get('material', 'N87')
            k, alpha, beta = self._get_steinmetz_coefficients(material)
            
            freq = requirements.get('frequency_Hz', 0)
            Bmax = core.get('Bmax_T', 0.2)
            Ve_cm3 = core.get('Ve_cm3', 0)
            Ve_m3 = Ve_cm3 * 1e-6
            
            if freq <= 0 or Ve_m3 <= 0:
                return None
            
            # Steinmetz calculation
            f_kHz = freq / 1000
            waveform = requirements.get('waveform', 'square')
            duty_cycle = requirements.get('duty_cycle_percent', 50) / 100
            Bac = calculate_Bac_from_waveform(Bmax, waveform, duty_cycle)
            loss_density = k * (f_kHz ** alpha) * (Bac ** beta)  # kW/m³
            Pcore_ref = loss_density * Ve_m3 * 1000  # W
            
            diff_pct = abs(Pcore_calc - Pcore_ref) / Pcore_ref * 100 if Pcore_ref > 0 else 0
            
            # Core loss validation has more uncertainty
            status = self._get_status(diff_pct, pass_thresh=10, warn_thresh=30)
            
            return ValidationResult(
                parameter="core_loss_W",
                our_value=round(Pcore_calc, 3),
                reference_value=round(Pcore_ref, 3),
                unit="W",
                difference_percent=round(diff_pct, 2),
                status=status,
                confidence=ConfidenceLevel.MEDIUM,
                source="Steinmetz equation",
                notes=f"k={k:.2e}, α={alpha}, β={beta}"
            )
            
        except Exception as e:
            logger.warning(f"Core loss validation error: {e}")
            return None
    
    def _validate_flux_density(
        self,
        design: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Validate operating flux density is within safe bounds.
        
        For ferrite: Bmax < 80% of Bsat (with margin for temperature)
        """
        try:
            core = design.get('core', {})
            
            Bmax = core.get('Bmax_T', 0)
            Bsat = core.get('Bsat_T', 0.4)
            
            if Bmax <= 0 or Bsat <= 0:
                return None
            
            # Reference: 70% of Bsat is safe operating point
            B_ref = Bsat * 0.7
            
            # Check if we're safely below saturation
            margin_to_sat = (Bsat - Bmax) / Bsat * 100
            
            if Bmax > Bsat * 0.9:
                status = ValidationStatus.FAIL
            elif Bmax > Bsat * 0.8:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.PASS
            
            return ValidationResult(
                parameter="flux_density_T",
                our_value=round(Bmax, 4),
                reference_value=round(B_ref, 4),
                unit="T",
                difference_percent=round(margin_to_sat, 1),
                status=status,
                confidence=ConfidenceLevel.HIGH,
                source="Saturation limit",
                notes=f"{margin_to_sat:.1f}% margin to Bsat={Bsat}T"
            )
            
        except Exception as e:
            logger.warning(f"Flux validation error: {e}")
            return None
    
    def _validate_thermal(
        self,
        design: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Validate thermal estimate using empirical formula.
        
        Tr = 450 * (Ptotal/At)^0.826 (°C) - McLyman's empirical formula
        """
        try:
            thermal = design.get('thermal', {})
            losses = design.get('losses', {})
            core = design.get('core', {})
            
            Tr_calc = thermal.get('temperature_rise_C', 0)
            if Tr_calc == 0:
                return None
            
            Ptotal = losses.get('total_loss_W', 0)
            At_cm2 = core.get('At_cm2', 0)
            
            if Ptotal <= 0 or At_cm2 <= 0:
                return None
            
            # McLyman's empirical formula
            psi = Ptotal / At_cm2  # W/cm²
            Tr_ref = 450 * (psi ** 0.826)
            
            diff_pct = abs(Tr_calc - Tr_ref) / Tr_ref * 100 if Tr_ref > 0 else 0
            
            status = self._get_status(diff_pct, pass_thresh=10, warn_thresh=25)
            
            return ValidationResult(
                parameter="temperature_rise_C",
                our_value=round(Tr_calc, 1),
                reference_value=round(Tr_ref, 1),
                unit="°C",
                difference_percent=round(diff_pct, 2),
                status=status,
                confidence=ConfidenceLevel.MEDIUM,
                source="McLyman empirical formula",
                notes=f"Ψ = {psi:.3f} W/cm²"
            )
            
        except Exception as e:
            logger.warning(f"Thermal validation error: {e}")
            return None
    
    def _validate_efficiency(
        self,
        design: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Validate efficiency is within expected range.
        
        Efficiency should be between specified target and theoretical maximum.
        """
        try:
            losses = design.get('losses', {})
            
            eta_calc = losses.get('efficiency_percent', 0)
            eta_target = requirements.get('efficiency_percent', 95)
            
            if eta_calc <= 0:
                return None
            
            # For power transformers, typical efficiency range
            Pout = requirements.get('output_power_W', 0)
            
            # Expected efficiency based on power level (empirical)
            if Pout < 100:
                eta_expected = 90  # Small transformers less efficient
            elif Pout < 1000:
                eta_expected = 95
            elif Pout < 10000:
                eta_expected = 97
            else:
                eta_expected = 98
            
            diff_pct = abs(eta_calc - eta_expected) / eta_expected * 100
            
            if eta_calc < eta_target * 0.95:  # More than 5% below target
                status = ValidationStatus.FAIL
            elif eta_calc < eta_target:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.PASS
            
            return ValidationResult(
                parameter="efficiency_percent",
                our_value=round(eta_calc, 2),
                reference_value=round(eta_expected, 2),
                unit="%",
                difference_percent=round(diff_pct, 2),
                status=status,
                confidence=ConfidenceLevel.MEDIUM,
                source="Expected for power level",
                notes=f"Target: {eta_target}%"
            )
            
        except Exception as e:
            logger.warning(f"Efficiency validation error: {e}")
            return None
    
    def _validate_window_utilization(
        self,
        design: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Validate window utilization is reasonable.
        
        Ku should be 0.2-0.5 for practical designs.
        """
        try:
            winding = design.get('winding', {})
            
            Ku_calc = winding.get('total_Ku', 0)
            
            if Ku_calc <= 0:
                return None
            
            # Reference: 0.35-0.40 is typical target
            Ku_ref = 0.4
            
            diff_pct = abs(Ku_calc - Ku_ref) / Ku_ref * 100
            
            if Ku_calc > 0.6:
                status = ValidationStatus.FAIL
                notes = "Window overfilled - reduce wire size or turns"
            elif Ku_calc > 0.5:
                status = ValidationStatus.WARNING
                notes = "Window nearly full - tight fit"
            elif Ku_calc < 0.2:
                status = ValidationStatus.WARNING
                notes = "Low utilization - core may be oversized"
            else:
                status = ValidationStatus.PASS
                notes = "Good window utilization"
            
            return ValidationResult(
                parameter="window_utilization_Ku",
                our_value=round(Ku_calc, 3),
                reference_value=Ku_ref,
                unit="ratio",
                difference_percent=round(diff_pct, 1),
                status=status,
                confidence=ConfidenceLevel.HIGH,
                source="Typical practice",
                notes=notes
            )
            
        except Exception as e:
            logger.warning(f"Ku validation error: {e}")
            return None
    
    def _validate_against_openmagnetics(
        self,
        design: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> List[ValidationResult]:
        """
        Cross-validate against OpenMagnetics database.
        
        Compares:
        - Our core loss vs OpenMagnetics model
        - Material Steinmetz coefficients
        """
        results = []
        
        if not self._om_db:
            return results
        
        try:
            core = design.get('core', {})
            losses = design.get('losses', {})
            
            material_name = core.get('material', '')
            if not material_name:
                return results
            
            # Get material properties from OpenMagnetics
            mat_props = self._om_db.get_material_properties(material_name)
            if mat_props is None:
                return results
            
            # Compare Steinmetz coefficients
            # Our values from design vs OpenMagnetics
            freq = requirements.get('frequency_Hz', 100000)
            Bmax = core.get('Bmax_T', 0.2)
            Ve_cm3 = core.get('Ve_cm3', 1.0)
            Ve_m3 = Ve_cm3 * 1e-6
            
            # Calculate loss using OpenMagnetics coefficients
            f_kHz = freq / 1000
            waveform = requirements.get('waveform', 'square')
            duty_cycle = requirements.get('duty_cycle_percent', 50) / 100
            Bac = calculate_Bac_from_waveform(Bmax, waveform, duty_cycle)
            om_loss_density = mat_props.steinmetz_k * (f_kHz ** mat_props.steinmetz_alpha) * (Bac ** mat_props.steinmetz_beta)
            om_core_loss = om_loss_density * Ve_m3 * 1000
            
            our_core_loss = losses.get('core_loss_W', 0)
            
            if om_core_loss > 0:
                diff_pct = abs(our_core_loss - om_core_loss) / om_core_loss * 100
                
                results.append(ValidationResult(
                    parameter="core_loss_vs_openmagnetics",
                    our_value=round(our_core_loss, 3),
                    reference_value=round(om_core_loss, 3),
                    unit="W",
                    difference_percent=round(diff_pct, 2),
                    status=self._get_status(diff_pct, pass_thresh=15, warn_thresh=30),
                    confidence=ConfidenceLevel.MEDIUM,
                    source="OpenMagnetics database",
                    notes=f"Material: {mat_props.name}, family: {mat_props.family}"
                ))
            
        except Exception as e:
            logger.warning(f"OpenMagnetics validation error: {e}")
        
        return results
    
    def _get_steinmetz_coefficients(self, material: str) -> Tuple[float, float, float]:
        """Get Steinmetz coefficients for a material."""
        # Default coefficients for common materials
        # k [kW/m³], alpha, beta (for f in kHz, B in T)
        coefficients = {
            'N87': (1.5e-6, 1.35, 2.45),
            'N97': (0.8e-6, 1.25, 2.35),
            'N49': (2.0e-6, 1.40, 2.55),
            '3C95': (1.4e-6, 1.30, 2.50),
            '3F35': (1.1e-6, 1.35, 2.45),
            'PC95': (1.2e-6, 1.25, 2.40),
        }
        
        # Find matching material
        for key, coeff in coefficients.items():
            if key.upper() in material.upper():
                return coeff
        
        # Default ferrite
        return (1.5e-6, 1.3, 2.5)
    
    def _get_status(
        self,
        diff_pct: float,
        pass_thresh: float = None,
        warn_thresh: float = None,
    ) -> ValidationStatus:
        """Determine validation status from percentage difference."""
        pass_t = pass_thresh or self.PASS_THRESHOLD
        warn_t = warn_thresh or self.WARNING_THRESHOLD
        
        if diff_pct <= pass_t:
            return ValidationStatus.PASS
        elif diff_pct <= warn_t:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.FAIL
    
    def _calculate_overall_status(self, report: CrossValidationReport):
        """Calculate overall validation status and confidence."""
        if not report.validations:
            report.overall_status = ValidationStatus.UNKNOWN
            report.overall_confidence = 0.0
            report.summary = "No validations performed"
            return
        
        # Count statuses
        fail_count = sum(1 for v in report.validations if v.status == ValidationStatus.FAIL)
        warn_count = sum(1 for v in report.validations if v.status == ValidationStatus.WARNING)
        pass_count = sum(1 for v in report.validations if v.status == ValidationStatus.PASS)
        
        total = len(report.validations)
        
        # Determine overall status
        if fail_count > 0:
            report.overall_status = ValidationStatus.FAIL
        elif warn_count > total / 2:
            report.overall_status = ValidationStatus.WARNING
        else:
            report.overall_status = ValidationStatus.PASS
        
        # Calculate confidence score (0-1)
        confidence_weights = {
            ConfidenceLevel.HIGH: 1.0,
            ConfidenceLevel.MEDIUM: 0.7,
            ConfidenceLevel.LOW: 0.4,
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for v in report.validations:
            weight = confidence_weights.get(v.confidence, 0.5)
            if v.status == ValidationStatus.PASS:
                score = 1.0
            elif v.status == ValidationStatus.WARNING:
                score = 0.7
            else:
                score = 0.3
            
            weighted_score += score * weight
            total_weight += weight
        
        report.overall_confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Generate summary
        report.summary = (
            f"Validation: {pass_count} pass, {warn_count} warning, {fail_count} fail "
            f"(confidence: {report.overall_confidence:.0%})"
        )
        
        # Generate recommendations
        for v in report.validations:
            if v.status == ValidationStatus.FAIL:
                report.recommendations.append(
                    f"CRITICAL: {v.parameter} differs by {v.difference_percent:.1f}% from {v.source}"
                )
            elif v.status == ValidationStatus.WARNING:
                report.recommendations.append(
                    f"Review: {v.parameter} - {v.notes}"
                )


def create_validation_dict(report: CrossValidationReport) -> Dict[str, Any]:
    """Convert CrossValidationReport to dictionary for API response."""
    return {
        "design_method": report.design_method,
        "overall_status": report.overall_status.value,
        "overall_confidence": round(report.overall_confidence, 3),
        "summary": report.summary,
        "recommendations": report.recommendations,
        "validations": {
            v.parameter: {
                "our_value": v.our_value,
                "reference_value": v.reference_value,
                "difference_percent": v.difference_percent,
                "status": v.status.value,
                "confidence": v.confidence.value,
                "unit": v.unit,
                "source": v.source,
                "notes": v.notes,
            }
            for v in report.validations
        },
    }