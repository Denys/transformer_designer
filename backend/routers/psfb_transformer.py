"""
PSFB Transformer Design API
"""

from fastapi import APIRouter, HTTPException
from models.psfb_transformer import PSFBDesignRequest, PSFBDesignResult
from calculations.psfb_transformer import design_for_target_leakage, calculate_leakage_inductance_shell
from calculations.losses import calculate_core_loss_igse
from integrations.openmagnetics import get_openmagnetics_db
import math

router = APIRouter(prefix="/api/design/psfb", tags=["psfb_transformer"])

@router.post("/design", response_model=PSFBDesignResult)
async def design_psfb_transformer(request: PSFBDesignRequest):
    """
    Design a Phase Shifted Full Bridge (PSFB) transformer.
    Focuses on leakage inductance targeting for ZVS.
    """

    # 1. Select Core (Simplified Ap method)
    # Ap = P * 10^4 / (K * B * f * J)
    # Assume B=0.1T, J=400 A/cm2, K=0.4
    Ap_needed = (request.power_W * 1e4) / (0.4 * 0.1 * (request.frequency_Hz/1000) * 400)

    db = get_openmagnetics_db()
    cores = db.find_suitable_cores(
        required_Ap_cm4=Ap_needed,
        frequency_Hz=request.frequency_Hz,
        preferred_geometry=request.core_geometry
    )

    if not cores:
        raise HTTPException(status_code=404, detail="No suitable core found")

    core = cores[0]

    # 2. Calculate Turns
    # N = V / (4 * B * Ae * f)
    Ae_m2 = core['Ae_cm2'] * 1e-4
    B_target = 0.15 # Tesla

    N_pri = max(1, int(request.input_voltage_V / (4 * B_target * Ae_m2 * request.frequency_Hz)))
    turns_ratio = request.input_voltage_V / request.output_voltage_V
    N_sec = max(1, int(N_pri / turns_ratio))

    # Recalculate B
    B_op = request.input_voltage_V / (4 * N_pri * Ae_m2 * request.frequency_Hz)

    # 3. Winding Geometry (Estimate)
    # Assume window filled 40%
    window_height_m = (core.get('height_mm', 20) / 2) * 1e-3 # Rough estimate
    window_width_m = (core.get('width_mm', 20) / 2) * 1e-3

    winding_width = window_height_m * 0.8 # Bobbin height

    # Radial build
    total_build = window_width_m * 0.4 # 40% fill
    h_pri = total_build / 2
    h_sec = total_build / 2
    MLT_m = core.get('MLT_cm', 5.0) * 1e-2

    # 4. Leakage Inductance Targeting
    shim_gap = 0.0
    Llk_achieved = 0.0
    target_met = True

    if request.target_leakage_uH:
        required_d = design_for_target_leakage(
            target_Llk_H=request.target_leakage_uH * 1e-6,
            N_primary=N_pri,
            MLT_m=MLT_m,
            winding_width_m=winding_width,
            primary_height_m=h_pri,
            secondary_height_m=h_sec
        )

        if required_d < 0:
            target_met = False
            shim_gap = 0.0001 # Min spacing
        else:
            shim_gap = required_d

        # Recalculate actual
        res = calculate_leakage_inductance_shell(
            N_primary=N_pri,
            N_secondary=N_sec,
            MLT_m=MLT_m,
            winding_width_m=winding_width,
            primary_height_m=h_pri,
            secondary_height_m=h_sec,
            insulation_thickness_m=shim_gap
        )
        Llk_achieved = res.Llk_total_referred_primary_H

    else:
        # Natural leakage
        res = calculate_leakage_inductance_shell(
            N_primary=N_pri,
            N_secondary=N_sec,
            MLT_m=MLT_m,
            winding_width_m=winding_width,
            primary_height_m=h_pri,
            secondary_height_m=h_sec,
            insulation_thickness_m=0.0005 # 0.5mm default
        )
        Llk_achieved = res.Llk_total_referred_primary_H

    # 5. Losses (iGSE for core)
    # Approximate trapezoidal waveform for PSFB? Or square for now.
    # For square wave, iGSE ~ Steinmetz if duty is 50%.
    # Let's construct a trapezoidal waveform with 100ns rise time
    T_period = 1.0 / request.frequency_Hz
    tr = 100e-9
    if tr > T_period/4: tr = T_period/4

    # Voltage waveform points (V, t)
    # 0 -> VCC (tr) -> VCC (T/2 - tr) -> 0 (tr) -> -VCC ...
    # Just one cycle is enough? iGSE averages integral.
    time_pts = [0, tr, T_period/2 - tr, T_period/2, T_period/2 + tr, T_period - tr, T_period]
    v_pts = [0, request.input_voltage_V, request.input_voltage_V, 0, -request.input_voltage_V, -request.input_voltage_V, 0]

    # Ferrite params (N87-like)
    k, alpha, beta = 8.1e-7, 1.46, 2.75 # From losses.py example

    core_loss = calculate_core_loss_igse(
        k=k, alpha=alpha, beta=beta,
        voltage_waveform=v_pts,
        time_points=time_pts,
        Ae_m2=Ae_m2,
        N_turns=N_pri,
        volume_cm3=core.get('Ve_cm3', 10.0) # Need Ve
    )

    # Copper loss (simplified DC)
    # R = rho * L / A
    # Ap = Wa * Ae. We estimated Ap.
    # Let's assume J=4A/mm2
    I_pri = request.power_W / request.input_voltage_V
    I_sec = request.power_W / request.output_voltage_V

    # Vol = MLT * N * A_wire
    # Pcu = Vol * rho_cu * J^2?
    # Pcu approx 0.5 * P_total_allowed?
    copper_loss = core_loss # Optimal design assumption

    total_loss = core_loss + copper_loss
    eff = (request.power_W / (request.power_W + total_loss)) * 100

    return PSFBDesignResult(
        core_part_number=core.get('part_number', 'Unknown'),
        turns_ratio=turns_ratio,
        primary_turns=N_pri,
        secondary_turns=N_sec,
        magnetizing_inductance_uH=1000.0, # Placeholder
        leakage_inductance_uH=Llk_achieved * 1e6,
        target_leakage_achieved=target_met,
        required_shim_gap_mm=shim_gap * 1000,
        core_loss_W=core_loss,
        copper_loss_W=copper_loss,
        total_loss_W=total_loss,
        efficiency_percent=eff,
        temp_rise_C=40.0, # Placeholder
        warnings=[] if target_met else ["Could not achieve target leakage with this core"]
    )
