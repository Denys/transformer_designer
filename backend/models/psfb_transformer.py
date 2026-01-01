"""
Pydantic models for PSFB transformer design
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PSFBDesignRequest(BaseModel):
    """Request model for PSFB transformer design."""

    # Input specifications
    power_W: float = Field(..., gt=0, description="Output power [W]")
    input_voltage_V: float = Field(..., gt=0, description="Input voltage [V]")
    output_voltage_V: float = Field(..., gt=0, description="Output voltage [V]")
    frequency_Hz: float = Field(..., gt=0, description="Switching frequency [Hz]")

    # ZVS Requirements
    target_leakage_uH: Optional[float] = Field(None, gt=0, description="Target leakage inductance for ZVS [uH]")
    max_leakage_uH: Optional[float] = Field(None, gt=0, description="Maximum allowed leakage [uH]")

    # Constraints
    max_temp_rise_C: float = Field(40.0, gt=0, description="Max temperature rise")
    core_geometry: Optional[str] = Field(None, description="Preferred core geometry (e.g. 'EE', 'PQ')")


class PSFBDesignResult(BaseModel):
    """Result model for PSFB transformer design."""

    core_part_number: str
    turns_ratio: float
    primary_turns: int
    secondary_turns: int

    # Electrical
    magnetizing_inductance_uH: float
    leakage_inductance_uH: float
    target_leakage_achieved: bool
    required_shim_gap_mm: float

    # Losses (using iGSE for core)
    core_loss_W: float
    copper_loss_W: float
    total_loss_W: float

    efficiency_percent: float
    temp_rise_C: float

    warnings: List[str]
