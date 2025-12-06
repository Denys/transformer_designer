"""
Inductor design API endpoints
"""

import json
import math
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from models.inductor import (
    InductorRequirements,
    InductorDesignResult,
    InductorWindingDesign,
)
from models.transformer import (
    CoreSelection,
    LossAnalysis,
    ThermalAnalysis,
    VerificationStatus,
)
from calculations.ap_method import (
    calculate_area_product_inductor,
    select_flux_density,
)
from calculations.winding import (
    calculate_wire_area,
    select_wire_gauge,
    calculate_dc_resistance,
    calculate_ac_resistance_factor,
)
from calculations.losses import (
    calculate_core_loss_steinmetz,
    calculate_copper_loss,
    calculate_total_losses,
)
from calculations.thermal import (
    calculate_surface_area,
    thermal_analysis,
)

router = APIRouter(prefix="/api", tags=["Inductor Design"])

DATA_DIR = Path(__file__).parent.parent / "data"


def load_cores():
    with open(DATA_DIR / "cores.json") as f:
        return json.load(f)


def load_materials():
    with open(DATA_DIR / "materials.json") as f:
        return json.load(f)


def calculate_air_gap(
    inductance_H: float,
    turns: int,
    Ae_cm2: float,
    lm_cm: float,
    mu_i: float,
) -> dict:
    """
    Calculate required air gap for target inductance.
    
    Formula:
        lg = (0.4π × N² × Ae × 10⁻⁸ / L) - lm/μi
        
    Returns gap length and fringing factor.
    """
    # Constants
    mu_0 = 4 * math.pi * 1e-7  # H/m
    
    # Convert to SI
    Ae_m2 = Ae_cm2 * 1e-4
    lm_m = lm_cm * 1e-2
    
    # Reluctance needed for target inductance
    R_total = (turns ** 2) / inductance_H
    
    # Core reluctance (without gap)
    R_core = lm_m / (mu_0 * mu_i * Ae_m2)
    
    # Gap reluctance needed
    R_gap = R_total - R_core
    
    if R_gap <= 0:
        # No gap needed - core provides enough inductance
        return {
            "gap_mm": 0,
            "gap_needed": False,
            "fringing_factor": 1.0,
        }
    
    # Gap length (total, split between center and outer legs for EE)
    lg_m = R_gap * mu_0 * Ae_m2
    lg_mm = lg_m * 1000
    
    # Fringing factor (rough approximation)
    # F = 1 + (lg/√Ae) × ln(2G/lg) where G is core dimension
    G_mm = math.sqrt(Ae_cm2 * 100)  # Approximate core dimension
    if lg_mm > 0.01:
        F = 1 + (lg_mm / G_mm) * math.log(2 * G_mm / lg_mm)
    else:
        F = 1.0
    
    return {
        "gap_mm": lg_mm,
        "gap_needed": True,
        "fringing_factor": min(F, 2.0),  # Cap at 2.0 for sanity
    }


def calculate_flux_density_inductor(
    inductance_H: float,
    dc_current_A: float,
    ripple_current_A: float,
    turns: int,
    Ae_cm2: float,
    gap_mm: float,
    mu_i: float,
    lm_cm: float,
) -> dict:
    """
    Calculate DC, AC, and peak flux density for inductor.
    """
    mu_0 = 4 * math.pi * 1e-7
    Ae_m2 = Ae_cm2 * 1e-4
    lm_m = lm_cm * 1e-2
    lg_m = gap_mm * 1e-3
    
    # Effective permeability with gap
    if lg_m > 0:
        mu_eff = lm_m / (lm_m / mu_i + lg_m)
    else:
        mu_eff = mu_i
    
    # DC flux density: Bdc = μ₀ × μeff × N × Idc / lm
    Bdc = mu_0 * mu_eff * turns * dc_current_A / lm_m
    
    # AC flux density from ripple: Bac = L × ΔI / (N × Ae)
    delta_I = ripple_current_A / 2  # Peak-to-peak to amplitude
    Bac = inductance_H * delta_I / (turns * Ae_m2)
    
    # Peak flux
    Bpeak = Bdc + Bac
    
    return {
        "Bdc_T": Bdc,
        "Bac_T": Bac,
        "Bpeak_T": Bpeak,
        "mu_eff": mu_eff,
    }


@router.post("/design/inductor", response_model=InductorDesignResult)
async def design_inductor(requirements: InductorRequirements):
    """
    Design an inductor using the energy storage (Ap) method.
    
    Steps:
    1. Calculate energy storage and peak current
    2. Determine Bmax for material
    3. Calculate required Ap
    4. Select suitable core
    5. Calculate turns and gap
    6. Verify flux density margins
    7. Design winding
    8. Analyze losses and thermal
    """
    try:
        # Step 1: Calculate peak current and energy
        if requirements.peak_current_A:
            Ipk = requirements.peak_current_A
        else:
            Ipk = requirements.dc_current_A + requirements.ripple_current_A / 2
        
        L_H = requirements.inductance_uH * 1e-6
        energy_J = 0.5 * L_H * (Ipk ** 2)
        energy_uJ = energy_J * 1e6
        
        # Step 2: Determine Bmax
        if requirements.frequency_Hz > 1000:
            material_type = "ferrite"
            material_grade = requirements.preferred_material or "3C95"
        else:
            material_type = "powder" if requirements.allow_powder_cores else "ferrite"
            material_grade = requirements.preferred_material or "Kool_Mu"
        
        flux_info = select_flux_density(requirements.frequency_Hz, material_type)
        Bmax = flux_info["Bmax_T"] * (1 - requirements.Bmax_margin_percent / 100)
        
        # Step 3: Calculate required Ap
        Ap = calculate_area_product_inductor(
            L_H,
            Ipk,
            Bmax,
            requirements.max_current_density_A_cm2,
            Ku=0.35
        )
        
        # Step 4: Select core
        cores = load_cores()
        suitable = []
        
        # For inductors, prefer ferrite or powder cores
        for core in cores.get("ferrite_cores", []):
            if core["Ap_cm4"] >= Ap * 0.9:
                if requirements.preferred_core_geometry:
                    if core["geometry"].upper() == requirements.preferred_core_geometry.upper():
                        suitable.append(core)
                else:
                    suitable.append(core)
        
        if not suitable:
            raise HTTPException(
                status_code=404,
                detail=f"No suitable core found for Ap = {Ap:.3f} cm⁴"
            )
        
        suitable.sort(key=lambda c: c["Ap_cm4"])
        selected_core = suitable[0]
        
        # Build CoreSelection
        materials = load_materials()
        mat_data = materials.get(material_type, {}).get(material_grade, {})
        Bsat = selected_core.get("Bsat_T", mat_data.get("Bsat_T", 0.4))
        
        core = CoreSelection(
            manufacturer=selected_core["manufacturer"],
            part_number=selected_core["part_number"],
            geometry=selected_core["geometry"],
            material=selected_core.get("material", material_grade),
            Ae_cm2=selected_core["Ae_cm2"],
            Wa_cm2=selected_core["Wa_cm2"],
            Ap_cm4=selected_core["Ap_cm4"],
            MLT_cm=selected_core["MLT_cm"],
            lm_cm=selected_core["lm_cm"],
            Ve_cm3=selected_core.get("Ve_cm3", selected_core["Ae_cm2"] * selected_core["lm_cm"]),
            At_cm2=selected_core.get("At_cm2", calculate_surface_area(selected_core["Ap_cm4"], selected_core["geometry"])),
            weight_g=selected_core["weight_g"],
            Bsat_T=Bsat,
            Bmax_T=Bmax,
            mu_i=selected_core.get("mu_i", mat_data.get("mu_i", 2000)),
        )
        
        # Step 5: Calculate turns and gap
        # Start with turns estimate from Faraday's law
        # N = (L × Ipk) / (Bmax × Ae)
        N_initial = int((L_H * Ipk) / (Bmax * core.Ae_cm2 * 1e-4))
        N = max(5, N_initial)
        
        # Calculate gap
        gap_data = calculate_air_gap(
            L_H,
            N,
            core.Ae_cm2,
            core.lm_cm,
            core.mu_i
        )
        
        # Step 6: Verify flux density
        flux_data = calculate_flux_density_inductor(
            L_H,
            requirements.dc_current_A,
            requirements.ripple_current_A,
            N,
            core.Ae_cm2,
            gap_data["gap_mm"],
            core.mu_i,
            core.lm_cm
        )
        
        # Check saturation margin
        saturation_margin = (Bsat - flux_data["Bpeak_T"]) / Bsat * 100
        
        # If margin is low, increase turns or core size
        if saturation_margin < 10:
            # Try increasing turns
            N = int(N * 1.2)
            gap_data = calculate_air_gap(L_H, N, core.Ae_cm2, core.lm_cm, core.mu_i)
            flux_data = calculate_flux_density_inductor(
                L_H, requirements.dc_current_A, requirements.ripple_current_A,
                N, core.Ae_cm2, gap_data["gap_mm"], core.mu_i, core.lm_cm
            )
            saturation_margin = (Bsat - flux_data["Bpeak_T"]) / Bsat * 100
        
        # Step 7: Winding design
        Irms = math.sqrt(requirements.dc_current_A ** 2 + (requirements.ripple_current_A / (2 * math.sqrt(3))) ** 2)
        
        wire_area = calculate_wire_area(Irms, requirements.max_current_density_A_cm2)
        wire_info = select_wire_gauge(wire_area, requirements.frequency_Hz)
        
        # Window utilization
        total_wire_area = N * wire_info["area_cm2"] * 1.3  # 30% insulation factor
        Ku = total_wire_area / core.Wa_cm2
        Ku_status = "ok" if Ku < 0.5 else ("warning" if Ku < 0.6 else "error")
        
        layers = max(1, int(math.ceil(N / 20)))
        
        Rdc = calculate_dc_resistance(
            N,
            core.MLT_cm,
            wire_info["area_cm2"],
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        
        Fr = calculate_ac_resistance_factor(
            wire_info["diameter_mm"],
            requirements.frequency_Hz,
            layers
        )
        
        winding = InductorWindingDesign(
            turns=N,
            wire_awg=wire_info["awg"],
            wire_dia_mm=wire_info["diameter_mm"],
            strands=wire_info["strands"],
            layers=layers,
            Rdc_mOhm=Rdc * 1000,
            Rac_Rdc=Fr,
            window_utilization=Ku,
            Ku_status=Ku_status,
        )
        
        # Calculate actual inductance
        mu_0 = 4 * math.pi * 1e-7
        Ae_m2 = core.Ae_cm2 * 1e-4
        lm_m = core.lm_cm * 1e-2
        lg_m = gap_data["gap_mm"] * 1e-3
        
        if lg_m > 0:
            mu_eff = lm_m / (lm_m / core.mu_i + lg_m)
        else:
            mu_eff = core.mu_i
        
        L_calc = mu_0 * mu_eff * (N ** 2) * Ae_m2 / lm_m
        L_calc_uH = L_calc * 1e6
        L_tolerance = abs(L_calc_uH - requirements.inductance_uH) / requirements.inductance_uH * 100
        
        # Step 8: Losses
        core_loss_W, core_loss_density = calculate_core_loss_steinmetz(
            core.Ve_cm3,
            requirements.frequency_Hz,
            flux_data["Bac_T"],
            material_grade,
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        
        copper_loss_W = calculate_copper_loss(
            Rdc,
            Irms,
            Fr,
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        
        total_loss_data = calculate_total_losses(core_loss_W, copper_loss_W, 0)
        
        losses = LossAnalysis(
            core_loss_W=core_loss_W,
            core_loss_density_mW_cm3=core_loss_density,
            primary_copper_loss_W=copper_loss_W,
            secondary_copper_loss_W=0,
            total_copper_loss_W=copper_loss_W,
            total_loss_W=total_loss_data["total_loss_W"],
            efficiency_percent=100 * (1 - total_loss_data["total_loss_W"] / (0.5 * L_H * Ipk ** 2 * requirements.frequency_Hz)),
            Pfe_Pcu_ratio=total_loss_data["Pfe_Pcu_ratio"],
        )
        
        # Thermal
        thermal_data = thermal_analysis(
            total_loss_data["total_loss_W"],
            core.At_cm2,
            requirements.ambient_temp_C,
            requirements.max_temp_rise_C,
            requirements.cooling
        )
        
        thermal = ThermalAnalysis(
            power_dissipation_density_W_cm2=thermal_data["power_dissipation_density_W_cm2"],
            temperature_rise_C=thermal_data["temperature_rise_C"],
            hotspot_temp_C=thermal_data["hotspot_temp_C"],
            thermal_margin_C=thermal_data["margin_to_target_C"],
            thermal_status=thermal_data["status"].replace("ok", "pass").replace("error", "fail"),
            cooling_recommendation=thermal_data["cooling_recommendation"],
        )
        
        # Verification
        warnings = []
        errors = []
        recommendations = thermal_data.get("recommendations", [])
        
        if saturation_margin < 15:
            warnings.append(f"Low saturation margin: {saturation_margin:.1f}%")
        if saturation_margin < 0:
            errors.append(f"Core saturates: Bpeak = {flux_data['Bpeak_T']:.3f} T > Bsat = {Bsat:.3f} T")
        if Ku_status == "error":
            errors.append(f"Window overfill: Ku = {Ku:.2f}")
        if thermal_data["status"] == "error":
            errors.append(f"Thermal limit exceeded: Tr = {thermal_data['temperature_rise_C']:.1f}°C")
        if L_tolerance > 10:
            warnings.append(f"Inductance deviation: {L_tolerance:.1f}% from target")
        
        # Convert ok/warning/error to pass/warning/fail
        def convert_status(s: str) -> str:
            return s.replace("ok", "pass").replace("error", "fail")
        
        verification = VerificationStatus(
            electrical="pass" if saturation_margin >= 10 else ("warning" if saturation_margin >= 0 else "fail"),
            mechanical=convert_status(Ku_status),
            thermal=convert_status(thermal_data["status"]),
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
        )
        
        design_viable = len(errors) == 0
        confidence_score = 0.9 if design_viable and len(warnings) == 0 else (0.7 if design_viable else 0.3)
        
        return InductorDesignResult(
            energy_uJ=energy_uJ,
            calculated_Ap_cm4=Ap,
            core=core,
            air_gap_mm=gap_data["gap_mm"] if gap_data["gap_needed"] else None,
            gap_location="center" if gap_data["gap_needed"] else None,
            fringing_factor=gap_data["fringing_factor"],
            Bdc_T=flux_data["Bdc_T"],
            Bac_T=flux_data["Bac_T"],
            Bpeak_T=flux_data["Bpeak_T"],
            saturation_margin_percent=saturation_margin,
            winding=winding,
            calculated_inductance_uH=L_calc_uH,
            inductance_tolerance_percent=L_tolerance,
            losses=losses,
            thermal=thermal,
            verification=verification,
            design_viable=design_viable,
            confidence_score=confidence_score,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
