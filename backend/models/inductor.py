"""
Pydantic models for inductor design
Energy storage method per McLyman
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field

from .transformer import CoreSelection, LossAnalysis, ThermalAnalysis, VerificationStatus


class InductorRequirements(BaseModel):
    """Input requirements for inductor design"""
    
    # Inductance specification
    inductance_uH: float = Field(..., gt=0, description="Required inductance [μH]")
    
    # Current specifications
    dc_current_A: float = Field(..., ge=0, description="DC bias current [A]")
    ripple_current_A: float = Field(..., gt=0, description="Peak-to-peak ripple current [A]")
    peak_current_A: Optional[float] = Field(default=None, description="Peak current [A], auto-calculated if not provided")
    
    # Frequency
    frequency_Hz: float = Field(..., gt=0, description="Switching frequency [Hz]")
    
    # Operating conditions
    ambient_temp_C: float = Field(default=40, ge=-40, le=85, description="Ambient temperature [°C]")
    max_temp_rise_C: float = Field(default=50, ge=20, le=100, description="Maximum temperature rise [°C]")
    cooling: Literal["natural", "forced"] = Field(default="natural", description="Cooling method")
    
    # Design preferences
    preferred_core_geometry: Optional[str] = Field(default=None, description="Preferred core geometry")
    preferred_material: Optional[str] = Field(default=None, description="Preferred core material")
    allow_gapped_ferrite: bool = Field(default=True, description="Allow gapped ferrite cores")
    allow_powder_cores: bool = Field(default=True, description="Allow powder cores (MPP, Kool Mμ)")
    
    # Current density limits
    max_current_density_A_cm2: float = Field(default=400, ge=100, le=800, description="Max current density [A/cm²]")
    
    # Saturation margin
    Bmax_margin_percent: float = Field(default=20, ge=10, le=40, description="Margin below Bsat [%]")


class InductorWindingDesign(BaseModel):
    """Inductor winding design"""
    
    turns: int = Field(..., ge=1, description="Number of turns")
    wire_awg: int = Field(..., ge=0, le=50, description="Wire gauge AWG")
    wire_dia_mm: float = Field(..., gt=0, description="Wire diameter [mm]")
    strands: int = Field(default=1, ge=1, description="Number of parallel strands")
    layers: int = Field(..., ge=1, description="Number of layers")
    
    Rdc_mOhm: float = Field(..., ge=0, description="DC resistance [mΩ]")
    Rac_Rdc: float = Field(default=1.0, ge=1.0, description="AC/DC resistance ratio")
    
    window_utilization: float = Field(..., ge=0, le=1, description="Window utilization Ku")
    Ku_status: Literal["ok", "warning", "error"] = Field(..., description="Window fill status")


class InductorDesignResult(BaseModel):
    """Complete inductor design output"""
    
    # Energy storage
    energy_uJ: float = Field(..., ge=0, description="Stored energy [μJ]")
    calculated_Ap_cm4: float = Field(..., ge=0, description="Calculated area product [cm⁴]")
    
    # Core selection
    core: CoreSelection
    
    # Gap (if applicable)
    air_gap_mm: Optional[float] = Field(default=None, description="Air gap length [mm]")
    gap_location: Optional[Literal["center", "distributed"]] = Field(default=None, description="Gap location")
    fringing_factor: float = Field(default=1.0, ge=1.0, description="Fringing factor F")
    
    # Flux density
    Bdc_T: float = Field(..., ge=0, description="DC flux density [T]")
    Bac_T: float = Field(..., ge=0, description="AC flux density [T]")
    Bpeak_T: float = Field(..., ge=0, description="Peak flux density [T]")
    saturation_margin_percent: float = Field(..., ge=0, description="Margin to saturation [%]")
    
    # Winding
    winding: InductorWindingDesign
    
    # Actual inductance
    calculated_inductance_uH: float = Field(..., gt=0, description="Calculated inductance [μH]")
    inductance_tolerance_percent: float = Field(..., ge=0, description="Inductance deviation [%]")
    
    # Analysis
    losses: LossAnalysis
    thermal: ThermalAnalysis
    verification: VerificationStatus
    
    # Summary
    design_viable: bool = Field(..., description="Is the design viable?")
    confidence_score: float = Field(..., ge=0, le=1, description="Design confidence score")
