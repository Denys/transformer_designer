"""
High-voltage insulation design

Implements IEC 60664 insulation coordination and
winding build-up calculations for HV transformers.
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
from .pulse_transformer import calculate_insulation_requirements, InsulationRequirements


@dataclass
class HVWindingBuild:
    """Result of HV winding build calculation."""
    num_layers: int
    turns_per_layer: int
    winding_height_mm: float
    winding_width_mm: float
    creepage_achieved_mm: float
    margin_tape_width_mm: float
    is_feasible: bool
    notes: List[str]


def winding_build_hv(
    turns: int,
    wire_diameter_mm: float,
    bobbin_winding_length_mm: float,
    bobbin_winding_depth_mm: float,
    required_creepage_mm: float,
    layer_insulation_thickness_mm: float = 0.05,
    insulation_layers_per_layer: int = 1,
) -> HVWindingBuild:
    """
    Calculate HV winding build-up with proper margins for creepage.

    For HV windings, we need "margin tape" on both sides of the winding
    to satisfy creepage requirements.

    Effective winding width = Bobbin length - 2 * Margin

    Args:
        turns: Total number of turns
        wire_diameter_mm: Wire diameter (including insulation) [mm]
        bobbin_winding_length_mm: Available length on bobbin [mm]
        bobbin_winding_depth_mm: Available depth on bobbin [mm]
        required_creepage_mm: Required creepage distance [mm]
        layer_insulation_thickness_mm: Thickness of insulation between layers [mm]
        insulation_layers_per_layer: Number of wraps of insulation tape

    Returns:
        HVWindingBuild object
    """
    notes = []

    # Margin calculation
    # For basic insulation, margin ≈ creepage / 2 (since path goes up and down margin)
    # Actually, creepage is the surface distance.
    # If we put margin tape of width M, the path from layer N to layer N+1
    # is M (across tape surface) + layer_insulation_thickness?
    # Usually, margin tape width IS the creepage distance provided at the ends of the winding.
    margin_width_mm = required_creepage_mm

    if margin_width_mm * 2 >= bobbin_winding_length_mm:
        return HVWindingBuild(
            num_layers=0,
            turns_per_layer=0,
            winding_height_mm=0,
            winding_width_mm=0,
            creepage_achieved_mm=0,
            margin_tape_width_mm=margin_width_mm,
            is_feasible=False,
            notes=[f"Required creepage {required_creepage_mm}mm x 2 exceeds bobbin length {bobbin_winding_length_mm}mm"]
        )

    effective_winding_length_mm = bobbin_winding_length_mm - (2 * margin_width_mm)

    # Wire packing (assume 90% linear fill factor)
    turns_per_layer = int(effective_winding_length_mm / wire_diameter_mm * 0.9)
    if turns_per_layer < 1:
        return HVWindingBuild(
            num_layers=0,
            turns_per_layer=0,
            winding_height_mm=0,
            winding_width_mm=0,
            creepage_achieved_mm=margin_width_mm,
            margin_tape_width_mm=margin_width_mm,
            is_feasible=False,
            notes=["Wire too large for available winding width after margins"]
        )

    num_layers = int((turns + turns_per_layer - 1) / turns_per_layer)

    # Total build height
    # Layer height = wire_dia + insulation
    layer_insulation_total = layer_insulation_thickness_mm * insulation_layers_per_layer
    total_height_mm = num_layers * (wire_diameter_mm + layer_insulation_total)

    is_feasible = True
    if total_height_mm > bobbin_winding_depth_mm:
        is_feasible = False
        notes.append(f"Winding height {total_height_mm:.1f}mm exceeds available depth {bobbin_winding_depth_mm}mm")

    return HVWindingBuild(
        num_layers=num_layers,
        turns_per_layer=turns_per_layer,
        winding_height_mm=total_height_mm,
        winding_width_mm=effective_winding_length_mm,
        creepage_achieved_mm=margin_width_mm,
        margin_tape_width_mm=margin_width_mm,
        is_feasible=is_feasible,
        notes=notes
    )


def recommend_insulation_system(
    voltage_class_V: float,
    temp_class_C: int = 155,
) -> Dict[str, str]:
    """
    Recommend insulation materials based on voltage and temperature.

    Args:
        voltage_class_V: Operating voltage class [V]
        temp_class_C: Temperature class (130, 155, 180, 220)

    Returns:
        Dictionary of recommended materials
    """
    system = {}

    # Wire Insulation
    if temp_class_C >= 200:
        system["wire"] = "Polyimide (Kapton) or PAI enamel (Class 220)"
    elif temp_class_C >= 180:
        system["wire"] = "Polyester-imide (Class 180)"
    else:
        system["wire"] = "Polyurethane/Nylon (Class 155)"

    if voltage_class_V > 1000:
        system["wire"] += " - Triple Insulated Wire (TIW) recommended for primary"

    # Layer Insulation
    if temp_class_C >= 200:
        system["layer"] = "Kapton (Polyimide) tape"
    elif temp_class_C >= 180:
        system["layer"] = "Nomex 410"
    else:
        system["layer"] = "Polyester film (Mylar) tape"

    # Margin Tape
    system["margin"] = system["layer"]

    # Impregnation
    if voltage_class_V > 1000:
        system["varnish"] = "Epoxy vacuum impregnation (necessary for HV to prevent corona)"
    else:
        system["varnish"] = "Polyester varnish dip"

    return system
