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
from .erickson_method import (
    calculate_Kg_erickson,
    calculate_Kgfe_erickson,
    design_transformer_erickson,
    optimal_Bac_for_minimum_loss,
)
from .winding import (
    calculate_turns,
    calculate_wire_area,
    awg_to_mm,
    mm_to_awg,
    calculate_skin_depth,
    calculate_dc_resistance,
    calculate_ac_resistance_factor,
    recommend_litz_wire,
    select_wire_for_frequency,
)
from .losses import (
    calculate_core_loss_steinmetz,
    calculate_copper_loss,
    calculate_total_losses,
    calculate_Bac_from_waveform,
)
from .thermal import (
    calculate_surface_area,
    calculate_power_dissipation_density,
    calculate_temperature_rise,
)
from .cross_validation import (
    TransformerValidator,
    CrossValidationReport,
    ValidationResult,
    ValidationStatus,
    ConfidenceLevel,
    create_validation_dict,
)

__all__ = [
    # ap_method
    "calculate_apparent_power",
    "calculate_area_product",
    "calculate_area_product_inductor",
    "waveform_coefficient",
    # kg_method (McLyman)
    "calculate_electrical_coefficient",
    "calculate_core_geometry",
    # erickson_method
    "calculate_Kg_erickson",
    "calculate_Kgfe_erickson",
    "design_transformer_erickson",
    "optimal_Bac_for_minimum_loss",
    # winding
    "calculate_turns",
    "calculate_wire_area",
    "awg_to_mm",
    "mm_to_awg",
    "calculate_skin_depth",
    "calculate_dc_resistance",
    "calculate_ac_resistance_factor",
    "recommend_litz_wire",
    "select_wire_for_frequency",
    # losses
    "calculate_core_loss_steinmetz",
    "calculate_copper_loss",
    "calculate_total_losses",
    "calculate_Bac_from_waveform",
    # thermal
    "calculate_surface_area",
    "calculate_power_dissipation_density",
    "calculate_temperature_rise",
    # cross_validation
    "TransformerValidator",
    "CrossValidationReport",
    "ValidationResult",
    "ValidationStatus",
    "ConfidenceLevel",
    "create_validation_dict",
]

