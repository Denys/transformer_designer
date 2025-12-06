"""Calculation modules for transformer and inductor design"""

from .ap_method import (
    calculate_apparent_power,
    calculate_area_product,
    calculate_area_product_inductor,
    waveform_coefficient,
)
from .kg_method import (
    calculate_electrical_coefficient,
    calculate_core_geometry,
)
from .winding import (
    calculate_turns,
    calculate_wire_area,
    awg_to_mm,
    mm_to_awg,
    calculate_skin_depth,
    calculate_dc_resistance,
    calculate_ac_resistance_factor,
)
from .losses import (
    calculate_core_loss_steinmetz,
    calculate_copper_loss,
    calculate_total_losses,
)
from .thermal import (
    calculate_surface_area,
    calculate_power_dissipation_density,
    calculate_temperature_rise,
)

__all__ = [
    # ap_method
    "calculate_apparent_power",
    "calculate_area_product",
    "calculate_area_product_inductor",
    "waveform_coefficient",
    # kg_method
    "calculate_electrical_coefficient",
    "calculate_core_geometry",
    # winding
    "calculate_turns",
    "calculate_wire_area",
    "awg_to_mm",
    "mm_to_awg",
    "calculate_skin_depth",
    "calculate_dc_resistance",
    "calculate_ac_resistance_factor",
    # losses
    "calculate_core_loss_steinmetz",
    "calculate_copper_loss",
    "calculate_total_losses",
    # thermal
    "calculate_surface_area",
    "calculate_power_dissipation_density",
    "calculate_temperature_rise",
]
