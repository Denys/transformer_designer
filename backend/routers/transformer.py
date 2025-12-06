"""
Transformer design API endpoints
"""

import json
from pathlib import Path
from typing import List, Optional, Union
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.transformer import (
    TransformerRequirements,
    TransformerDesignResult,
    CoreSelection,
    WindingDesign,
    LossAnalysis,
    ThermalAnalysis,
    VerificationStatus,
    DesignSuggestion,
    CoreAlternative,
    NoMatchResult,
)
from calculations.ap_method import (
    calculate_apparent_power,
    calculate_area_product,
    waveform_coefficient,
    select_flux_density,
)
from calculations.kg_method import (
    calculate_electrical_coefficient,
    calculate_core_geometry,
    kg_to_ap,
    select_design_method,
)
from calculations.winding import (
    calculate_turns,
    calculate_wire_area,
    select_wire_gauge,
    calculate_dc_resistance,
    calculate_ac_resistance_factor,
    calculate_window_utilization,
)
from calculations.losses import (
    calculate_core_loss_steinmetz,
    calculate_copper_loss,
    calculate_total_losses,
    calculate_efficiency,
)
from calculations.thermal import (
    calculate_surface_area,
    thermal_analysis,
)
from calculations.validation import (
    validate_core_loss,
    validate_efficiency,
    validate_temperature_rise,
    run_full_validation,
)

router = APIRouter(prefix="/api", tags=["Transformer Design"])

# Load core database
DATA_DIR = Path(__file__).parent.parent / "data"


def load_cores():
    """Load core database from JSON"""
    with open(DATA_DIR / "cores.json") as f:
        return json.load(f)


def load_materials():
    """Load materials database from JSON"""
    with open(DATA_DIR / "materials.json") as f:
        return json.load(f)


def find_suitable_cores(
    required_Ap_cm4: float,
    frequency_Hz: float,
    preferred_geometry: Optional[str] = None,
    preferred_material: Optional[str] = None,
) -> List[dict]:
    """
    Find cores that meet the Ap requirement from LOCAL database only.
    Returns cores sorted by Ap (smallest suitable first).
    """
    cores = load_cores()
    suitable = []
    
    # Determine material type from frequency
    if frequency_Hz > 1000:
        core_list = cores.get("ferrite_cores", [])
    else:
        core_list = cores.get("silicon_steel_cores", [])
    
    for core in core_list:
        # Check Ap requirement (with 10% margin)
        if core["Ap_cm4"] >= required_Ap_cm4 * 0.9:
            # Filter by geometry if specified
            if preferred_geometry and core["geometry"].upper() != preferred_geometry.upper():
                continue
            # Filter by material if specified
            if preferred_material and preferred_material.lower() not in core["material"].lower():
                continue
            # Tag as local source
            core_copy = dict(core)
            core_copy["source"] = "local"
            suitable.append(core_copy)
    
    # Sort by Ap (smallest first)
    suitable.sort(key=lambda c: c["Ap_cm4"])
    
    return suitable


def find_suitable_cores_hybrid(
    required_Ap_cm4: float,
    frequency_Hz: float,
    preferred_geometry: Optional[str] = None,
    preferred_material: Optional[str] = None,
    include_openmagnetics: bool = True,
) -> List[dict]:
    """
    Find cores from BOTH local database AND OpenMagnetics.
    Returns combined list sorted by Ap (smallest suitable first).
    """
    # First, try local database
    local_cores = find_suitable_cores(
        required_Ap_cm4, frequency_Hz, preferred_geometry, preferred_material
    )
    
    if not include_openmagnetics:
        return local_cores
    
    # Also search OpenMagnetics
    try:
        from integrations.openmagnetics import get_openmagnetics_db
        om_db = get_openmagnetics_db()
        
        if om_db.is_available:
            om_cores = om_db.get_cores(
                min_Ap_cm4=required_Ap_cm4 * 0.9,
                max_Ap_cm4=required_Ap_cm4 * 3.0,  # Don't go too oversized
                shape_family=preferred_geometry,
                material=preferred_material,
                limit=20,
            )
            
            # Filter by frequency suitability and add to list
            for core in om_cores:
                # High freq needs ferrite materials
                if frequency_Hz > 1000:
                    mat = core.get('material', '').upper()
                    ferrite_families = ['3C', '3F', '3E', 'N', 'PC', 'P', 'R', 'T']
                    if not any(mat.startswith(f) for f in ferrite_families):
                        continue
                local_cores.append(core)
    except Exception as e:
        # If OpenMagnetics fails, just use local cores
        pass
    
    # Sort combined list by Ap
    local_cores.sort(key=lambda c: c["Ap_cm4"])
    
    return local_cores



def get_largest_available_core(frequency_Hz: float) -> dict:
    """Get the largest core available for given frequency range"""
    cores = load_cores()
    if frequency_Hz > 1000:
        core_list = cores.get("ferrite_cores", [])
    else:
        core_list = cores.get("silicon_steel_cores", [])
    
    if not core_list:
        return {"Ap_cm4": 0}
    
    return max(core_list, key=lambda c: c["Ap_cm4"])


def get_closest_cores(required_Ap_cm4: float, frequency_Hz: float, count: int = 3) -> List[dict]:
    """Get the closest available cores by Ap"""
    cores = load_cores()
    if frequency_Hz > 1000:
        core_list = cores.get("ferrite_cores", [])
    else:
        core_list = cores.get("silicon_steel_cores", [])
    
    # Sort by distance from required Ap, preferring larger cores
    core_list = sorted(core_list, key=lambda c: c["Ap_cm4"], reverse=True)
    return core_list[:count]


def calculate_max_power_for_core(
    core: dict,
    frequency_Hz: float,
    Bmax_T: float,
    J_A_cm2: float,
    Ku: float,
    Kf: float,
) -> float:
    """Calculate maximum power a core can handle"""
    # Ap = Pt × 10^4 / (Kf × Ku × Bmax × J × f)
    # Pt = Ap × Kf × Ku × Bmax × J × f / 10^4
    Ap = core["Ap_cm4"]
    Pt = (Ap * Kf * Ku * Bmax_T * J_A_cm2 * frequency_Hz) / 1e4
    # Pt is apparent power, output is roughly Pt/2 for efficiency
    return Pt * 0.45  # Assume ~90% efficiency


def generate_suggestions(
    requirements: TransformerRequirements,
    required_Ap: float,
    largest_core: dict,
    frequency_Hz: float,
    Bmax_T: float,
    Kf: float,
) -> NoMatchResult:
    """Generate helpful suggestions when no suitable core is found"""
    
    max_Ap = largest_core["Ap_cm4"]
    max_power = calculate_max_power_for_core(
        largest_core,
        frequency_Hz,
        Bmax_T,
        requirements.max_current_density_A_cm2,
        requirements.window_utilization_Ku,
        Kf,
    )
    
    suggestions = []
    
    # Suggestion 1: Reduce power
    if requirements.output_power_W > max_power:
        suggestions.append(DesignSuggestion(
            parameter="output_power_W",
            current_value=requirements.output_power_W,
            suggested_value=round(max_power * 0.9, 0),
            unit="W",
            impact=f"Largest available core ({largest_core['part_number']}) can handle up to ~{max_power:.0f}W",
            feasible=True
        ))
    
    # Suggestion 2: Increase frequency (reduces Ap requirement)
    if frequency_Hz < 500000:  # Only suggest if under 500kHz
        ratio = required_Ap / max_Ap
        suggested_freq = frequency_Hz * ratio * 1.1  # Add 10% margin
        if suggested_freq <= 500000:
            suggestions.append(DesignSuggestion(
                parameter="frequency_Hz",
                current_value=frequency_Hz,
                suggested_value=round(suggested_freq / 1000) * 1000,  # Round to nearest kHz
                unit="Hz",
                impact=f"Higher frequency reduces required Ap from {required_Ap:.1f} to ~{max_Ap:.1f} cm⁴",
                feasible=True
            ))
    
    # Suggestion 3: Increase current density (reduces wire size)
    if requirements.max_current_density_A_cm2 < 600:
        ratio = required_Ap / max_Ap
        suggested_J = requirements.max_current_density_A_cm2 * ratio
        if suggested_J <= 800:
            suggestions.append(DesignSuggestion(
                parameter="max_current_density_A_cm2",
                current_value=requirements.max_current_density_A_cm2,
                suggested_value=round(suggested_J / 50) * 50,
                unit="A/cm²",
                impact="Higher current density reduces wire size, allowing smaller core (increases losses)",
                feasible=suggested_J <= 600
            ))
    
    # Suggestion 4: Increase Ku (tighter winding)
    if requirements.window_utilization_Ku < 0.50:
        suggestions.append(DesignSuggestion(
            parameter="window_utilization_Ku",
            current_value=requirements.window_utilization_Ku,
            suggested_value=0.45,
            unit="",
            impact="Higher fill factor allows smaller core (requires careful winding)",
            feasible=True
        ))
    
    # Get closest cores
    closest = get_closest_cores(required_Ap, frequency_Hz, 3)
    closest_cores = []
    for core in closest:
        core_max_power = calculate_max_power_for_core(
            core, frequency_Hz, Bmax_T,
            requirements.max_current_density_A_cm2,
            requirements.window_utilization_Ku,
            Kf
        )
        closest_cores.append(CoreAlternative(
            part_number=core["part_number"],
            manufacturer=core["manufacturer"],
            geometry=core["geometry"],
            Ap_cm4=core["Ap_cm4"],
            max_power_W=core_max_power,
            notes=f"Largest {core['geometry']} core in database"
        ))
    
    # Alternative approaches
    alternatives = [
        "Consider using multiple smaller transformers in parallel",
        "Consider silicon steel cores for higher power at lower frequency (50-400Hz)",
        "Explore OpenMagnetics database for a wider core selection",
        "Custom core design may be required for this power level",
    ]
    if frequency_Hz > 100000:
        alternatives.insert(0, "Consider planar magnetics for this power/frequency combination")
    
    return NoMatchResult(
        success=False,
        message=f"Required Ap ({required_Ap:.1f} cm⁴) exceeds largest available core ({max_Ap:.1f} cm⁴)",
        required_Ap_cm4=required_Ap,
        available_max_Ap_cm4=max_Ap,
        suggestions=suggestions,
        closest_cores=closest_cores,
        alternative_approaches=alternatives,
    )


@router.post("/design/transformer", response_model=Union[TransformerDesignResult, NoMatchResult])
async def design_transformer(requirements: TransformerRequirements):
    """
    Design a transformer using McLyman's Ap/Kg methodology.
    
    Steps:
    1. Calculate apparent power
    2. Determine Bmax for frequency/material
    3. Calculate Ap or Kg based on regulation requirements
    4. Select suitable core
    5. Calculate winding design
    6. Analyze losses and thermal performance
    7. Verify design
    """
    try:
        # Step 1: Calculate apparent power
        Pt = calculate_apparent_power(
            requirements.output_power_W,
            requirements.efficiency_percent
        )
        
        # Step 2: Determine waveform coefficient and flux density
        Kf = waveform_coefficient(requirements.waveform.value)
        
        # Select material type based on frequency
        if requirements.frequency_Hz > 1000:
            material_type = "ferrite"
            material_grade = requirements.preferred_material or "N87"
        else:
            material_type = "silicon_steel"
            material_grade = requirements.preferred_material or "M6"
        
        flux_info = select_flux_density(requirements.frequency_Hz, material_type)
        Bmax = flux_info["Bmax_T"]
        
        # Step 3: Calculate Ap (and Kg if regulation is critical)
        design_method = select_design_method(
            requirements.regulation_percent,
            requirements.output_power_W,
            requirements.frequency_Hz  # Add frequency to method selection
        )
        
        if design_method == "Kg":
            Ke = calculate_electrical_coefficient(requirements.frequency_Hz, Bmax, Kf)
            Kg = calculate_core_geometry(Pt, requirements.regulation_percent, Ke)
            Ap = kg_to_ap(Kg, requirements.preferred_core_geometry or "EE")
        else:
            Kg = None
            Ap = calculate_area_product(
                Pt,
                requirements.frequency_Hz,
                Bmax,
                requirements.max_current_density_A_cm2,
                requirements.window_utilization_Ku,
                Kf
            )
        
        # Step 4: Select core (using hybrid search with OpenMagnetics)
        suitable_cores = find_suitable_cores_hybrid(
            Ap,
            requirements.frequency_Hz,
            requirements.preferred_core_geometry,
            requirements.preferred_material,
            include_openmagnetics=True  # Enable OpenMagnetics search
        )
        
        if not suitable_cores:
            # Instead of error, return helpful suggestions
            # Also check OpenMagnetics for larger cores
            largest_core = get_largest_available_core(requirements.frequency_Hz)
            return generate_suggestions(
                requirements,
                Ap,
                largest_core,
                requirements.frequency_Hz,
                Bmax,
                Kf,
            )
        
        selected_core_data = suitable_cores[0]  # Pick smallest suitable
        
        # Build CoreSelection model
        materials = load_materials()
        mat_data = materials.get(material_type, {}).get(material_grade, {})
        
        core = CoreSelection(
            manufacturer=selected_core_data["manufacturer"],
            part_number=selected_core_data["part_number"],
            geometry=selected_core_data["geometry"],
            material=selected_core_data.get("material", material_grade),
            source=selected_core_data.get("source", "local"),  # Track database source
            datasheet_url=selected_core_data.get("datasheet_url", None),  # Include datasheet link if available
            Ae_cm2=selected_core_data["Ae_cm2"],
            Wa_cm2=selected_core_data["Wa_cm2"],
            Ap_cm4=selected_core_data["Ap_cm4"],
            MLT_cm=selected_core_data.get("MLT_cm", 5.0),  # Default for OpenMagnetics cores
            lm_cm=selected_core_data.get("lm_cm", 5.0),
            Ve_cm3=selected_core_data.get("Ve_cm3", selected_core_data["Ae_cm2"] * selected_core_data.get("lm_cm", 5.0)),
            At_cm2=selected_core_data.get("At_cm2", calculate_surface_area(selected_core_data["Ap_cm4"], selected_core_data["geometry"])),
            weight_g=selected_core_data.get("weight_g", 100),  # Default for OpenMagnetics
            Bsat_T=selected_core_data.get("Bsat_T", mat_data.get("Bsat_T", 0.4)),
            Bmax_T=Bmax,
            mu_i=selected_core_data.get("mu_i", mat_data.get("mu_i", 2000)),
        )
        
        # Step 5: Winding design
        # Primary turns
        Np = calculate_turns(
            requirements.primary_voltage_V,
            requirements.frequency_Hz,
            Bmax,
            core.Ae_cm2,
            Kf
        )
        
        # Secondary turns
        turns_ratio = requirements.secondary_voltage_V / requirements.primary_voltage_V
        Ns = max(1, round(Np * turns_ratio))
        actual_ratio = Ns / Np
        
        # Currents
        primary_current_A = Pt / (2 * requirements.primary_voltage_V)  # Approx
        secondary_current_A = requirements.output_power_W / requirements.secondary_voltage_V
        
        # Wire sizing
        primary_wire_area = calculate_wire_area(
            primary_current_A,
            requirements.max_current_density_A_cm2
        )
        secondary_wire_area = calculate_wire_area(
            secondary_current_A,
            requirements.max_current_density_A_cm2
        )
        
        primary_wire = select_wire_gauge(
            primary_wire_area,
            requirements.frequency_Hz
        )
        secondary_wire = select_wire_gauge(
            secondary_wire_area,
            requirements.frequency_Hz
        )
        
        # DC resistance
        primary_Rdc = calculate_dc_resistance(
            Np,
            core.MLT_cm,
            primary_wire["area_cm2"],
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        secondary_Rdc = calculate_dc_resistance(
            Ns,
            core.MLT_cm,
            secondary_wire["area_cm2"],
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        
        # AC resistance factors
        primary_layers = max(1, Np // 20)  # Rough estimate
        secondary_layers = max(1, Ns // 20)
        
        primary_Fr = calculate_ac_resistance_factor(
            primary_wire["diameter_mm"],
            requirements.frequency_Hz,
            primary_layers
        )
        secondary_Fr = calculate_ac_resistance_factor(
            secondary_wire["diameter_mm"],
            requirements.frequency_Hz,
            secondary_layers
        )
        
        # Window utilization
        window_util = calculate_window_utilization(
            Np, primary_wire["area_cm2"],
            Ns, secondary_wire["area_cm2"],
            core.Wa_cm2
        )
        
        winding = WindingDesign(
            primary_turns=Np,
            primary_wire_awg=primary_wire["awg"],
            primary_wire_dia_mm=primary_wire["diameter_mm"],
            primary_strands=primary_wire["strands"],
            primary_layers=primary_layers,
            primary_Rdc_mOhm=primary_Rdc * 1000,
            primary_Rac_Rdc=primary_Fr,
            secondary_turns=Ns,
            secondary_wire_awg=secondary_wire["awg"],
            secondary_wire_dia_mm=secondary_wire["diameter_mm"],
            secondary_strands=secondary_wire["strands"],
            secondary_layers=secondary_layers,
            secondary_Rdc_mOhm=secondary_Rdc * 1000,
            secondary_Rac_Rdc=secondary_Fr,
            total_Ku=window_util["Ku"],
            Ku_status=window_util["status"],
        )
        
        # Step 6: Loss analysis
        # Core loss
        core_loss_W, core_loss_density = calculate_core_loss_steinmetz(
            core.Ve_cm3,
            requirements.frequency_Hz,
            Bmax / 2,  # Bac = Bm/2 for transformer
            material_grade,
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        
        # Copper losses
        primary_Pcu = calculate_copper_loss(
            primary_Rdc,
            primary_current_A,
            primary_Fr,
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        secondary_Pcu = calculate_copper_loss(
            secondary_Rdc,
            secondary_current_A,
            secondary_Fr,
            requirements.ambient_temp_C + requirements.max_temp_rise_C / 2
        )
        
        total_loss_data = calculate_total_losses(
            core_loss_W,
            primary_Pcu,
            secondary_Pcu
        )
        
        efficiency = calculate_efficiency(
            requirements.output_power_W,
            total_loss_data["total_loss_W"]
        )
        
        losses = LossAnalysis(
            core_loss_W=core_loss_W,
            core_loss_density_mW_cm3=core_loss_density,
            primary_copper_loss_W=primary_Pcu,
            secondary_copper_loss_W=secondary_Pcu,
            total_copper_loss_W=total_loss_data["total_copper_loss_W"],
            total_loss_W=total_loss_data["total_loss_W"],
            efficiency_percent=efficiency,
            Pfe_Pcu_ratio=total_loss_data["Pfe_Pcu_ratio"],
        )
        
        # Step 7: Thermal analysis
        thermal_data = thermal_analysis(
            total_loss_data["total_loss_W"],
            core.At_cm2,
            requirements.ambient_temp_C,
            requirements.max_temp_rise_C,
            requirements.cooling,
            material_max_temp_C=120 if material_type == "ferrite" else 150
        )
        
        thermal = ThermalAnalysis(
            power_dissipation_density_W_cm2=thermal_data["power_dissipation_density_W_cm2"],
            temperature_rise_C=thermal_data["temperature_rise_C"],
            hotspot_temp_C=thermal_data["hotspot_temp_C"],
            thermal_margin_C=thermal_data["margin_to_target_C"],
            thermal_status=thermal_data["status"].replace("error", "fail").replace("ok", "pass"),
            cooling_recommendation=thermal_data["cooling_recommendation"],
        )
        
        # Verification
        warnings = []
        errors = []
        recommendations = thermal_data.get("recommendations", [])
        
        # Check window utilization
        if window_util["status"] == "error":
            errors.append(f"Window overfill: Ku = {window_util['Ku']:.2f} > 0.6")
        elif window_util["status"] == "warning":
            warnings.append(f"Window fill marginal: Ku = {window_util['Ku']:.2f}")
        
        # Check thermal
        if thermal_data["status"] == "error":
            errors.append(f"Thermal limit exceeded: Tr = {thermal_data['temperature_rise_C']:.1f}°C")
        elif thermal_data["status"] == "warning":
            warnings.append(f"Thermal margin low: {thermal_data['margin_to_target_C']:.1f}°C")
        
        # Check efficiency
        if efficiency < requirements.efficiency_percent:
            warnings.append(f"Efficiency {efficiency:.1f}% below target {requirements.efficiency_percent}%")
        
        # Check flux density margin
        Bmax_margin = (core.Bsat_T - Bmax) / core.Bsat_T * 100
        if Bmax_margin < 15:
            warnings.append(f"Low saturation margin: {Bmax_margin:.1f}% below Bsat")
        
        # Convert ok/warning/error to pass/warning/fail
        def convert_status(s: str) -> str:
            return s.replace("ok", "pass").replace("error", "fail")
        
        verification = VerificationStatus(
            electrical="pass" if not any("efficiency" in w.lower() for w in warnings + errors) else "warning",
            mechanical=convert_status(window_util["status"]),
            thermal=convert_status(thermal_data["status"]),
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
        )
        
        # Design viability
        design_viable = len(errors) == 0
        confidence_score = 0.9 if design_viable and len(warnings) == 0 else (0.7 if design_viable else 0.3)
        
        # Get alternative cores (up to 3 others that also work)
        alternative_cores = []
        for alt_core in suitable_cores[1:4]:  # Skip first (selected), take next 3
            alternative_cores.append({
                "part_number": alt_core.get("part_number"),
                "manufacturer": alt_core.get("manufacturer"),
                "geometry": alt_core.get("geometry"),
                "material": alt_core.get("material", "N87"),
                "Ap_cm4": alt_core.get("Ap_cm4"),
                "source": alt_core.get("source", "local"),
                "datasheet_url": alt_core.get("datasheet_url"),
            })
        
        # Method names for display
        method_names = {
            "Ap": "McLyman Ap (Area Product)",
            "Kg": "McLyman Kg (Regulation)",
            "Kgfe": "Erickson Kgfe (Loss Optimized)",
        }
        
        # Run validation against reference data
        validation_results = {}
        
        # Core loss validation
        core_loss_val = validate_core_loss(
            our_loss_W=core_loss_W,
            volume_cm3=core.Ve_cm3,
            frequency_Hz=requirements.frequency_Hz,
            Bac_T=Bmax / 2,
            material=material_grade,
            temperature_C=requirements.ambient_temp_C + thermal_data["temperature_rise_C"] / 2,
        )
        validation_results["core_loss"] = {
            "our_value": round(core_loss_val.our_value, 2),
            "reference_value": round(core_loss_val.reference_value, 2),
            "difference_percent": round(core_loss_val.difference_percent, 1),
            "status": core_loss_val.status,
            "confidence": core_loss_val.confidence,
            "unit": "mW/cm³",
        }
        
        # Efficiency validation
        eff_val = validate_efficiency(
            calculated_efficiency=efficiency,
            output_power_W=requirements.output_power_W,
            frequency_Hz=requirements.frequency_Hz,
            core_volume_cm3=core.Ve_cm3,
        )
        validation_results["efficiency"] = {
            "our_value": round(eff_val.our_value, 1),
            "reference_value": round(eff_val.reference_value, 1),
            "difference_percent": round(eff_val.difference_percent, 1),
            "status": eff_val.status,
            "confidence": eff_val.confidence,
            "unit": "%",
        }
        
        # Temperature rise validation
        temp_val = validate_temperature_rise(
            calculated_rise_C=thermal_data["temperature_rise_C"],
            power_dissipation_W=total_loss_data["total_loss_W"],
            surface_area_cm2=core.At_cm2,
            cooling=requirements.cooling,
        )
        validation_results["temperature_rise"] = {
            "our_value": round(temp_val.our_value, 1),
            "reference_value": round(temp_val.reference_value, 1),
            "difference_percent": round(temp_val.difference_percent, 1),
            "status": temp_val.status,
            "confidence": temp_val.confidence,
            "unit": "°C",
        }
        
        return TransformerDesignResult(
            design_method=design_method,
            design_method_name=method_names.get(design_method, "McLyman Ap"),
            calculated_Ap_cm4=Ap,
            calculated_Kg_cm5=Kg,
            optimal_Pfe_Pcu_ratio=1.375 if design_method == "Kgfe" else None,  # β/2 for β=2.75
            core=core,
            alternative_cores=alternative_cores,
            winding=winding,
            turns_ratio=actual_ratio,
            magnetizing_inductance_uH=None,  # Could calculate if needed
            leakage_inductance_uH=None,
            losses=losses,
            thermal=thermal,
            verification=verification,
            validation=validation_results,
            design_viable=design_viable,
            confidence_score=confidence_score,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cores")
async def list_cores(
    geometry: Optional[str] = None,
    material_type: Optional[str] = None,
    min_Ap_cm4: Optional[float] = None,
):
    """List available cores with optional filtering"""
    cores = load_cores()
    result = []
    
    for category, core_list in cores.items():
        for core in core_list:
            # Apply filters
            if geometry and core["geometry"].upper() != geometry.upper():
                continue
            if min_Ap_cm4 and core["Ap_cm4"] < min_Ap_cm4:
                continue
            if material_type:
                if material_type.lower() == "ferrite" and "ferrite" not in category:
                    continue
                if material_type.lower() in ["silicon_steel", "si_steel"] and "silicon" not in category:
                    continue
            
            result.append({
                "category": category,
                **core
            })
    
    return {"cores": result, "count": len(result)}


@router.get("/materials")
async def list_materials(material_type: Optional[str] = None):
    """List available materials with properties"""
    materials = load_materials()
    
    if material_type:
        if material_type.lower() in materials:
            return {material_type.lower(): materials[material_type.lower()]}
        else:
            raise HTTPException(status_code=404, detail=f"Material type '{material_type}' not found")
    
    return materials


@router.post("/validate/core-loss")
async def validate_core_loss_endpoint(
    core_loss_W: float,
    volume_cm3: float,
    frequency_Hz: float,
    Bac_T: float,
    material: str = "ferrite",
    temperature_C: float = 100,
):
    """
    Validate a core loss calculation against reference data.
    
    Returns comparison with manufacturer datasheet values and industry benchmarks.
    """
    result = validate_core_loss(
        our_loss_W=core_loss_W,
        volume_cm3=volume_cm3,
        frequency_Hz=frequency_Hz,
        Bac_T=Bac_T,
        material=material,
        temperature_C=temperature_C,
    )
    
    return {
        "our_value_mW_cm3": result.our_value,
        "reference_value_mW_cm3": result.reference_value,
        "difference_percent": round(result.difference_percent, 1),
        "status": result.status,
        "method": result.method,
        "notes": result.notes,
    }


@router.post("/validate/design")
async def validate_design_endpoint(
    design_result: dict,
    requirements: TransformerRequirements,
):
    """
    Run full validation suite on a transformer design.
    
    Validates core loss, efficiency, and temperature rise against reference data.
    """
    req_dict = requirements.model_dump()
    
    validations = run_full_validation(design_result, req_dict)
    
    return {
        name: {
            "our_value": v.our_value,
            "reference_value": v.reference_value,
            "difference_percent": round(v.difference_percent, 1),
            "status": v.status,
            "method": v.method,
            "notes": v.notes,
        }
        for name, v in validations.items()
    }

