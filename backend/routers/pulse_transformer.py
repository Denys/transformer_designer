"""
Pulse Transformer Design API endpoints

Provides design endpoints for:
- Gate drive transformers
- Signal isolation transformers
- High-voltage pulse transformers
- Trigger circuits
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from models.pulse_transformer import (
    PulseTransformerRequirements,
    PulseApplicationType,
    InsulationType,
    OvervoltageCategory,
    PollutionDegree,
    InsulationCalculationRequest,
    VoltSecondResult,
    PulseResponseAnalysis,
    InsulationResult,
    PulseTransformerWinding,
    PulseTransformerDesignResult,
    GateDriverPreset,
    GATE_DRIVER_PRESETS,
)
from calculations.pulse_transformer import (
    calculate_volt_second,
    design_for_volt_second,
    analyze_pulse_response,
    calculate_insulation_requirements,
    calculate_magnetizing_inductance,
    calculate_leakage_inductance,
    calculate_winding_capacitance,
)
from calculations.winding import awg_to_mm, calculate_dc_resistance
from integrations.openmagnetics import get_openmagnetics_db

import math
import json


router = APIRouter(prefix="/api/design/pulse", tags=["pulse_transformer"])


# ============================================================================
# Response Models
# ============================================================================

class VoltSecondResponse(BaseModel):
    """Volt-second calculation response."""
    volt_second_uVs: float
    volt_second_mVs: float
    required_Ae_cm2: float
    required_Ae_mm2: float
    Bmax_T: float
    primary_turns_min: int
    flux_swing_T: float


class InsulationResponse(BaseModel):
    """IEC 60664 insulation response."""
    clearance_mm: float
    creepage_mm: float
    solid_insulation_mm: float
    impulse_withstand_kV: float
    ac_withstand_Vrms: float
    recommended_materials: List[str]
    construction_notes: List[str]


class PulseResponseResponse(BaseModel):
    """Pulse response analysis response."""
    rise_time_ns: float
    fall_time_ns: float
    droop_percent: float
    backswing_percent: float
    bandwidth_3dB_MHz: float
    ringing_freq_MHz: Optional[float]
    overshoot_percent: float


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/volt-second", response_model=VoltSecondResponse)
async def calculate_volt_second_endpoint(
    voltage_V: float = Query(..., gt=0, description="Pulse voltage [V]"),
    pulse_width_us: float = Query(..., gt=0, description="Pulse width [µs]"),
    duty_cycle_percent: float = Query(50.0, ge=0.1, le=99, description="Duty cycle [%]"),
    Bmax_T: float = Query(0.2, gt=0, le=0.5, description="Max flux density [T]"),
    initial_turns: int = Query(10, ge=1, le=1000, description="Starting turns"),
):
    """
    Calculate volt-second product and core sizing.
    
    The volt-second product (V·µs) is the fundamental requirement for
    pulse transformers. This endpoint calculates:
    - Volt-second rating
    - Required core area (Ae)
    - Minimum primary turns
    """
    result = design_for_volt_second(
        voltage_V=voltage_V,
        pulse_width_us=pulse_width_us,
        duty_cycle_percent=duty_cycle_percent,
        Bmax_T=Bmax_T,
        initial_turns=initial_turns,
    )
    
    return VoltSecondResponse(
        volt_second_uVs=result.volt_second_uVs,
        volt_second_mVs=result.volt_second_mVs,
        required_Ae_cm2=result.required_Ae_cm2,
        required_Ae_mm2=result.required_Ae_mm2,
        Bmax_T=result.Bmax_T,
        primary_turns_min=result.primary_turns_min,
        flux_swing_T=result.flux_swing_T,
    )


@router.post("/insulation", response_model=InsulationResponse)
async def calculate_insulation_endpoint(request: InsulationCalculationRequest):
    """
    Calculate IEC 60664 insulation requirements.
    
    Returns clearance, creepage, and solid insulation requirements
    based on working voltage, insulation type, and environmental conditions.
    """
    result = calculate_insulation_requirements(
        working_voltage_Vrms=request.working_voltage_Vrms,
        insulation_type=request.insulation_type.value,
        overvoltage_category=request.overvoltage_category.value,
        pollution_degree=request.pollution_degree.value,
        altitude_m=request.altitude_m,
        material_group=request.material_group,
    )
    
    return InsulationResponse(
        clearance_mm=result.clearance_mm,
        creepage_mm=result.creepage_mm,
        solid_insulation_mm=result.solid_insulation_mm,
        impulse_withstand_kV=result.impulse_withstand_kV,
        ac_withstand_Vrms=result.ac_withstand_Vrms,
        recommended_materials=result.recommended_materials,
        construction_notes=result.construction_notes,
    )


@router.post("/pulse-response", response_model=PulseResponseResponse)
async def analyze_pulse_endpoint(
    magnetizing_inductance_uH: float = Query(..., gt=0, description="Magnetizing inductance [µH]"),
    leakage_inductance_nH: float = Query(..., gt=0, description="Leakage inductance [nH]"),
    winding_capacitance_pF: float = Query(..., ge=0, description="Winding capacitance [pF]"),
    load_resistance_ohm: float = Query(..., gt=0, description="Load resistance [Ω]"),
    pulse_voltage_V: float = Query(..., gt=0, description="Pulse voltage [V]"),
    pulse_width_us: float = Query(..., gt=0, description="Pulse width [µs]"),
):
    """
    Analyze pulse transformer response.
    
    Calculates rise time, droop, backswing, and bandwidth based on
    transformer parameters and load conditions.
    """
    result = analyze_pulse_response(
        magnetizing_inductance_uH=magnetizing_inductance_uH,
        leakage_inductance_nH=leakage_inductance_nH,
        winding_capacitance_pF=winding_capacitance_pF,
        load_resistance_ohm=load_resistance_ohm,
        pulse_voltage_V=pulse_voltage_V,
        pulse_width_us=pulse_width_us,
    )
    
    return PulseResponseResponse(
        rise_time_ns=result.rise_time_ns,
        fall_time_ns=result.fall_time_ns,
        droop_percent=result.droop_percent,
        backswing_percent=result.backswing_percent,
        bandwidth_3dB_MHz=result.bandwidth_3dB_MHz,
        ringing_freq_MHz=result.ringing_freq_MHz,
        overshoot_percent=result.overshoot_percent,
    )


@router.post("/design")
async def design_pulse_transformer(requirements: PulseTransformerRequirements):
    """
    Design a complete pulse transformer.
    
    Supports:
    - Gate drive transformers (HF, ferrite, Bmax ~0.2T)
    - HV power pulse transformers (LF, silicon-steel, Bmax ~1.2T) - like Dropless
    """
    # Determine if this is HV power pulse mode (energy transfer)
    is_hv_power_pulse = requirements.application == PulseApplicationType.HV_POWER_PULSE
    
    # Handle millisecond pulse width (convert to µs for calculations)
    pulse_width_us = requirements.pulse_width_us
    if requirements.pulse_width_ms:
        pulse_width_us = requirements.pulse_width_ms * 1000  # ms → µs
    
    # Select Bmax based on core material type and application
    if requirements.core_material_type:
        Bmax_by_type = {
            "ferrite": 0.2,
            "silicon_steel": 1.2,  # Much higher for silicon steel
            "amorphous": 1.0,
            "nanocrystalline": 0.8,
        }
        Bmax = Bmax_by_type.get(requirements.core_material_type.value, 0.2)
    elif is_hv_power_pulse or requirements.frequency_Hz < 1000:
        # Low frequency → silicon steel → high Bmax
        Bmax = 1.2
    else:
        # High frequency → ferrite → conservative Bmax
        Bmax = 0.2
    
    # Calculate volt-second requirement
    Vt_result = design_for_volt_second(
        voltage_V=requirements.primary_voltage_V,
        pulse_width_us=pulse_width_us,
        duty_cycle_percent=requirements.duty_cycle_percent,
        Bmax_T=Bmax,
        initial_turns=requirements.primary_turns or 10,
    )
    
    # Calculate insulation requirements
    insulation = calculate_insulation_requirements(
        working_voltage_Vrms=requirements.isolation_voltage_Vrms,
        insulation_type=requirements.insulation_type.value,
        overvoltage_category=requirements.overvoltage_category.value,
        pollution_degree=requirements.pollution_degree.value,
    )
    
    # Search for suitable core
    db = get_openmagnetics_db()
    
    # Estimate required Ap from Ae (Ap ≈ Ae × Wa, assume Wa ≈ 2×Ae for small cores)
    required_Ae_cm2 = Vt_result.required_Ae_cm2
    estimated_Ap = required_Ae_cm2 * (required_Ae_cm2 * 2)
    
    # For HV power pulse, prefer E/I laminated cores
    preferred_geom = requirements.preferred_core_geometry
    if is_hv_power_pulse and not preferred_geom:
        preferred_geom = "EI"  # Default to E/I laminated for power pulse
    
    cores = db.find_suitable_cores(
        required_Ap_cm4=estimated_Ap,
        frequency_Hz=requirements.frequency_Hz,
        preferred_geometry=preferred_geom,
        preferred_material=requirements.preferred_material,
        count=5,
    )
    
    if not cores:
        raise HTTPException(
            status_code=404,
            detail=f"No suitable cores found for Ae ≥ {required_Ae_cm2:.3f} cm² (Bmax={Bmax}T). For HV power pulse, consider specifying larger Ae manually."
        )
    
    # Select best core (first one that meets Ae requirement)
    selected_core = None
    for core in cores:
        if core.get('Ae_cm2', 0) >= required_Ae_cm2 * 0.9:
            selected_core = core
            break
    
    if not selected_core:
        selected_core = cores[0]  # Use largest available
    
    # Calculate turns ratio
    turns_ratio = requirements.secondary_voltage_V / requirements.primary_voltage_V
    
    # Use specified turns if provided (for HV power pulse)
    if requirements.primary_turns and requirements.secondary_turns:
        primary_turns = requirements.primary_turns
        secondary_turns = requirements.secondary_turns
    else:
        # Calculate primary turns from volt-second and actual Ae
        Ae_cm2 = selected_core.get('Ae_cm2', required_Ae_cm2)
        Ae_m2 = Ae_cm2 * 1e-4
        Vt_Vs = Vt_result.volt_second_uVs * 1e-6
        
        primary_turns = max(1, int(math.ceil(Vt_Vs / (Ae_m2 * Bmax))))
        secondary_turns = max(1, int(round(primary_turns * turns_ratio)))
    
    # For HV power pulse: validate turns ratio
    actual_ratio = secondary_turns / primary_turns if primary_turns > 0 else turns_ratio

    
    # Determine wire size based on peak current
    # For HV power pulse, primary current can be in kA range
    if requirements.peak_current_A:
        # For HV power pulse, peak_current_A is primary current
        if is_hv_power_pulse:
            Ip_peak = requirements.peak_current_A
        else:
            Ip_peak = requirements.peak_current_A / turns_ratio
    elif requirements.load_resistance_ohm:
        Ip_peak = requirements.secondary_voltage_V / requirements.load_resistance_ohm / turns_ratio
    else:
        Ip_peak = 1.0  # Default 1A
    
    # Wire sizing: use higher current density for pulse (5-10 A/mm² for short pulses)
    current_density = 5.0  # A/mm² - conservative
    if is_hv_power_pulse and pulse_width_us < 10000:  # < 10ms pulse
        current_density = 10.0  # Higher density OK for short pulses
    
    wire_area_mm2 = Ip_peak / current_density
    wire_dia_mm = math.sqrt(4 * wire_area_mm2 / math.pi)
    
    # For kA currents, use foil or cable instead of AWG
    if Ip_peak > 100:
        # Use foil or cable description instead of AWG
        primary_awg = None
        primary_wire_dia = wire_dia_mm
        primary_wire_type = "foil" if wire_area_mm2 > 50 else "cable"
    else:
        # Find nearest AWG (extend range for larger wires)
        # awg_to_mm returns (diameter_mm, area_mm2) tuple
        awg_table = [(awg, awg_to_mm(awg)[0]) for awg in range(10, 40)]  # AWG 10-40 range
        primary_awg = min(awg_table, key=lambda x: abs(x[1] - wire_dia_mm))[0]
        primary_wire_dia = awg_to_mm(primary_awg)[0]  # Get diameter from tuple
        primary_wire_type = "solid"
    
    # Secondary wire (scaled by turns ratio for current)
    secondary_current = Ip_peak / turns_ratio if turns_ratio > 1 else Ip_peak * turns_ratio
    secondary_wire_area = secondary_current / current_density
    secondary_wire_dia = math.sqrt(4 * secondary_wire_area / math.pi)
    
    if secondary_current > 100:
        secondary_awg = None
        secondary_wire_dia_actual = secondary_wire_dia
        secondary_wire_type = "foil" if secondary_wire_area > 50 else "cable"
    else:
        awg_table = [(awg, awg_to_mm(awg)[0]) for awg in range(10, 40)]  # Get diameter from tuple
        secondary_awg = min(awg_table, key=lambda x: abs(x[1] - secondary_wire_dia))[0]
        secondary_wire_dia_actual = awg_to_mm(secondary_awg)[0]  # Get diameter from tuple
        secondary_wire_type = "solid"
    
    # Calculate inductances
    lm_cm = selected_core.get('lm_cm', 3.0)
    lm_m = lm_cm * 1e-2
    mu_r = selected_core.get('mu_i', 2000)
    
    Lm = calculate_magnetizing_inductance(
        turns=primary_turns,
        Ae_m2=Ae_m2,
        lm_m=lm_m,
        mu_r=mu_r,
    )
    Lm_uH = Lm * 1e6
    
    # Leakage inductance (estimate)
    MLT_cm = selected_core.get('MLT_cm', 3.0)
    MLT_m = MLT_cm * 1e-2
    Wa_cm2 = selected_core.get('Wa_cm2', 0.5)
    window_height_m = math.sqrt(Wa_cm2) * 1e-2
    window_width_m = math.sqrt(Wa_cm2) * 1e-2 * 0.8
    
    Llk = calculate_leakage_inductance(
        turns=primary_turns,
        MLT_m=MLT_m,
        winding_height_m=window_height_m,
        winding_width_m=window_width_m,
        layer_spacing_m=insulation.solid_insulation_mm * 1e-3,
        num_layers=2,
    )
    Llk_nH = Llk * 1e9
    
    # Winding capacitance
    Cw = calculate_winding_capacitance(
        turns=primary_turns + secondary_turns,
        MLT_m=MLT_m,
        wire_diameter_m=primary_wire_dia * 1e-3,
        layer_spacing_m=insulation.solid_insulation_mm * 1e-3,
        insulation_thickness_m=0.05e-3,  # 50µm insulation
        num_layers=2,
    )
    Cw_pF = Cw * 1e12
    
    # Calculate DC resistance using (turns, MLT_cm, wire_area_cm2)
    primary_wire_area_cm2 = wire_area_mm2 * 1e-2  # mm² to cm²
    secondary_wire_area_cm2 = secondary_wire_area * 1e-2
    MLT_cm = MLT_m * 100
    
    primary_Rdc = calculate_dc_resistance(primary_turns, MLT_cm, primary_wire_area_cm2) * 1000  # mΩ
    secondary_Rdc = calculate_dc_resistance(secondary_turns, MLT_cm, secondary_wire_area_cm2) * 1000
    
    # Analyze pulse response
    load_R = requirements.load_resistance_ohm or 10  # Default 10Ω
    
    pulse_resp = analyze_pulse_response(
        magnetizing_inductance_uH=Lm_uH,
        leakage_inductance_nH=Llk_nH,
        winding_capacitance_pF=Cw_pF,
        load_resistance_ohm=load_R,
        pulse_voltage_V=requirements.primary_voltage_V,
        pulse_width_us=requirements.pulse_width_us,
    )
    
    # Check specifications
    warnings = []
    recommendations = []
    meets_specs = True
    
    if requirements.rise_time_ns and pulse_resp.rise_time_ns > requirements.rise_time_ns:
        warnings.append(f"Rise time {pulse_resp.rise_time_ns:.1f}ns exceeds requirement {requirements.rise_time_ns}ns")
        recommendations.append("Reduce leakage inductance by interleaving windings")
        meets_specs = False
    
    if pulse_resp.droop_percent > requirements.max_droop_percent:
        warnings.append(f"Droop {pulse_resp.droop_percent:.1f}% exceeds maximum {requirements.max_droop_percent}%")
        recommendations.append("Increase magnetizing inductance (more turns or higher µ core)")
        meets_specs = False
    
    if pulse_resp.backswing_percent > requirements.max_backswing_percent:
        warnings.append(f"Backswing {pulse_resp.backswing_percent:.1f}% exceeds maximum {requirements.max_backswing_percent}%")
        recommendations.append("Add snubber circuit or increase winding capacitance")
    
    # Estimate losses (simplified)
    # Core loss at operating frequency and Bmax (low duty cycle reduces average)
    duty = requirements.duty_cycle_percent / 100
    Pcore_mW = 10 * Ae_cm2 * duty  # Very rough estimate
    
    # Copper loss (DC approximation)
    Pcu_mW = (Ip_peak ** 2) * (primary_Rdc + secondary_Rdc / (turns_ratio ** 2)) * duty
    
    total_loss_mW = Pcore_mW + Pcu_mW
    
    # Temperature rise estimate
    At_cm2 = selected_core.get('At_cm2', 10)
    psi = total_loss_mW / 1000 / At_cm2  # W/cm²
    temp_rise = 450 * (psi ** 0.826) if psi > 0 else 0
    
    # Build response
    return {
        "application": requirements.application.value,
        "volt_second_uVs": Vt_result.volt_second_uVs,
        "turns_ratio": round(turns_ratio, 3),
        
        "core": {
            "part_number": selected_core.get('part_number', 'Unknown'),
            "manufacturer": selected_core.get('manufacturer', 'Unknown'),
            "geometry": selected_core.get('geometry', 'Unknown'),
            "material": selected_core.get('material', 'Unknown'),
            "Ae_cm2": Ae_cm2,
            "Ap_cm4": selected_core.get('Ap_cm4', 0),
            "source": selected_core.get('source', 'openmagnetics'),
        },
        
        "primary": {
            "turns": primary_turns,
            "wire_type": primary_wire_type if 'primary_wire_type' in dir() else "solid",
            "wire_awg": primary_awg,
            "wire_diameter_mm": round(primary_wire_dia, 3),
            "wire_area_mm2": round(wire_area_mm2, 2),
            "peak_current_A": round(Ip_peak, 1),
            "layers": 1,
            "Rdc_mOhm": round(primary_Rdc, 3),
            "inductance_uH": round(Lm_uH, 2),
        },
        
        "secondary": {
            "turns": secondary_turns,
            "wire_type": secondary_wire_type if 'secondary_wire_type' in dir() else "solid",
            "wire_awg": secondary_awg,
            "wire_diameter_mm": round(secondary_wire_dia_actual, 3),
            "wire_area_mm2": round(secondary_wire_area, 2),
            "layers": 1,
            "Rdc_mOhm": round(secondary_Rdc, 3),
        },
        
        "electrical": {
            "magnetizing_inductance_uH": round(Lm_uH, 2),
            "leakage_inductance_nH": round(Llk_nH, 2),
            "interwinding_capacitance_pF": round(Cw_pF, 2),
        },
        
        "pulse_response": {
            "rise_time_ns": pulse_resp.rise_time_ns,
            "fall_time_ns": pulse_resp.fall_time_ns,
            "droop_percent": pulse_resp.droop_percent,
            "backswing_percent": pulse_resp.backswing_percent,
            "bandwidth_3dB_MHz": pulse_resp.bandwidth_3dB_MHz,
            "ringing_freq_MHz": pulse_resp.ringing_freq_MHz,
            "overshoot_percent": pulse_resp.overshoot_percent,
        },
        
        "insulation": {
            "clearance_mm": insulation.clearance_mm,
            "creepage_mm": insulation.creepage_mm,
            "solid_insulation_mm": insulation.solid_insulation_mm,
            "impulse_withstand_kV": insulation.impulse_withstand_kV,
            "recommended_materials": insulation.recommended_materials,
            "construction_notes": insulation.construction_notes,
        },
        
        "thermal": {
            "core_loss_mW": round(Pcore_mW, 2),
            "copper_loss_mW": round(Pcu_mW, 2),
            "total_loss_mW": round(total_loss_mW, 2),
            "temperature_rise_C": round(temp_rise, 1),
        },
        
        "verification": {
            "meets_specifications": meets_specs,
            "warnings": warnings,
            "recommendations": recommendations,
        },
    }


@router.get("/presets")
async def get_gate_driver_presets():
    """
    Get predefined gate driver presets.
    
    Returns preset configurations for common gate driver applications
    including MOSFETs, IGBTs, SiC, and GaN devices.
    """
    return {
        "presets": {
            k: {
                "name": v.name,
                "description": v.description,
                "device_type": v.device_type,
                "typical_Vdrive": v.typical_Vdrive,
                "typical_Ipeak": v.typical_Ipeak,
                "typical_Qg_nC": v.typical_Qg_nC,
                "typical_ton_ns": v.typical_ton_ns,
                "typical_toff_ns": v.typical_toff_ns,
                "suggested_turns_ratio": v.suggested_turns_ratio,
                "suggested_Lm_min_uH": v.suggested_Lm_min_uH,
                "suggested_Llk_max_nH": v.suggested_Llk_max_nH,
            }
            for k, v in GATE_DRIVER_PRESETS.items()
        }
    }


@router.get("/applications")
async def get_application_types():
    """Get list of supported pulse transformer application types."""
    return {
        "applications": [
            {"id": e.value, "name": e.name.replace("_", " ").title()}
            for e in PulseApplicationType
        ]
    }


@router.get("/insulation-types")
async def get_insulation_types():
    """Get list of IEC 60664 insulation types."""
    return {
        "types": [
            {
                "id": e.value,
                "name": e.name.replace("_", " ").title(),
                "description": {
                    "functional": "Insulation necessary for correct operation",
                    "basic": "Insulation providing basic protection against electric shock",
                    "supplementary": "Independent insulation applied in addition to basic",
                    "double": "Basic + supplementary insulation",
                    "reinforced": "Single insulation equivalent to double",
                }.get(e.value, ""),
            }
            for e in InsulationType
        ]
    }