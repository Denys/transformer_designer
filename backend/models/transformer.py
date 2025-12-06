"""
Pydantic models for transformer design inputs and outputs
Based on McLyman's Ap/Kg and Erickson's Kgfe methodologies
"""

from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class TransformerType(str, Enum):
    """Type of transformer design"""
    POWER_LF = "power_lf"      # 50-400 Hz line frequency
    POWER_HF = "power_hf"      # kHz-MHz SMPS
    FLYBACK = "flyback"        # Flyback converter
    FORWARD = "forward"        # Forward converter
    PULSE = "pulse"            # Energy transfer / pulse


class WaveformType(str, Enum):
    """Input waveform type"""
    SINUSOIDAL = "sinusoidal"  # Kf = 4.44
    SQUARE = "square"          # Kf = 4.0
    TRIANGULAR = "triangular"  # Kf = 4.0
    PULSE = "pulse"            # Use volt-seconds method


class DesignMethod(str, Enum):
    """Design methodology selection"""
    AP_MCLYMAN = "ap_mclyman"        # McLyman Area Product - simple, general purpose
    KG_MCLYMAN = "kg_mclyman"        # McLyman Kg - regulation focused (low freq)
    KGFE_ERICKSON = "kgfe_erickson"  # Erickson Kgfe - loss optimized (high freq)
    AUTO = "auto"                    # Automatically select best method


class TransformerRequirements(BaseModel):
    """Input requirements for transformer design"""
    
    # Power specifications
    output_power_W: float = Field(..., gt=0, description="Output power [W]")
    efficiency_percent: float = Field(default=90, ge=50, le=99.9, description="Target efficiency [%]")
    regulation_percent: float = Field(default=5, ge=0.5, le=20, description="Voltage regulation [%]")
    
    # Voltage specifications
    primary_voltage_V: float = Field(..., gt=0, description="Primary voltage [V RMS or DC]")
    secondary_voltage_V: float = Field(..., gt=0, description="Secondary voltage [V]")
    
    # Frequency and waveform
    frequency_Hz: float = Field(..., gt=0, description="Operating frequency [Hz]")
    waveform: WaveformType = Field(default=WaveformType.SINUSOIDAL, description="Input waveform type")
    duty_cycle: Optional[float] = Field(default=0.5, ge=0.1, le=0.9, description="Duty cycle for switching converters")
    
    # Operating conditions
    ambient_temp_C: float = Field(default=40, ge=-40, le=85, description="Ambient temperature [°C]")
    max_temp_rise_C: float = Field(default=50, ge=20, le=100, description="Maximum temperature rise [°C]")
    cooling: Literal["natural", "forced"] = Field(default="natural", description="Cooling method")
    
    # Design preferences
    transformer_type: TransformerType = Field(default=TransformerType.POWER_HF, description="Transformer type")
    preferred_core_geometry: Optional[str] = Field(default=None, description="Preferred core geometry (EE, ETD, PQ, etc.)")
    preferred_material: Optional[str] = Field(default=None, description="Preferred core material")
    design_method: DesignMethod = Field(default=DesignMethod.AUTO, description="Design methodology")
    
    # Current density limits
    max_current_density_A_cm2: float = Field(default=400, ge=100, le=800, description="Max current density [A/cm²]")
    
    # Window utilization
    window_utilization_Ku: float = Field(default=0.35, ge=0.15, le=0.55, description="Window utilization factor")


class CoreSelection(BaseModel):
    """Selected core parameters"""
    
    manufacturer: str = Field(..., description="Core manufacturer")
    part_number: str = Field(..., description="Core part number")
    geometry: str = Field(..., description="Core geometry (EE, ETD, PQ, etc.)")
    material: str = Field(..., description="Core material grade")
    source: str = Field(default="local", description="Database source (local, openmagnetics)")
    datasheet_url: Optional[str] = Field(default=None, description="Link to manufacturer datasheet")
    
    # Core dimensions
    Ae_cm2: float = Field(..., gt=0, description="Effective cross-sectional area [cm²]")
    Wa_cm2: float = Field(..., gt=0, description="Window area [cm²]")
    Ap_cm4: float = Field(..., gt=0, description="Area product [cm⁴]")
    MLT_cm: float = Field(..., gt=0, description="Mean length per turn [cm]")
    lm_cm: float = Field(..., gt=0, description="Magnetic path length [cm]")
    Ve_cm3: float = Field(..., gt=0, description="Effective volume [cm³]")
    At_cm2: float = Field(..., gt=0, description="Surface area for cooling [cm²]")
    weight_g: float = Field(..., gt=0, description="Core weight [g]")
    
    # Material properties
    Bsat_T: float = Field(..., gt=0, description="Saturation flux density [T]")
    Bmax_T: float = Field(..., gt=0, description="Operating flux density [T]")
    mu_i: float = Field(..., gt=0, description="Initial permeability")


class WindingDesign(BaseModel):
    """Winding design parameters"""
    
    # Primary winding
    primary_turns: int = Field(..., ge=1, description="Primary turns")
    primary_wire_awg: int = Field(..., ge=0, le=50, description="Primary wire gauge AWG")
    primary_wire_dia_mm: float = Field(..., gt=0, description="Primary wire diameter [mm]")
    primary_strands: int = Field(default=1, ge=1, description="Number of parallel strands")
    primary_layers: int = Field(..., ge=1, description="Number of primary layers")
    primary_Rdc_mOhm: float = Field(..., ge=0, description="Primary DC resistance [mΩ]")
    primary_Rac_Rdc: float = Field(default=1.0, ge=1.0, description="AC/DC resistance ratio")
    
    # Secondary winding
    secondary_turns: int = Field(..., ge=1, description="Secondary turns")
    secondary_wire_awg: int = Field(..., ge=0, le=50, description="Secondary wire gauge AWG")
    secondary_wire_dia_mm: float = Field(..., gt=0, description="Secondary wire diameter [mm]")
    secondary_strands: int = Field(default=1, ge=1, description="Number of parallel strands")
    secondary_layers: int = Field(..., ge=1, description="Number of secondary layers")
    secondary_Rdc_mOhm: float = Field(..., ge=0, description="Secondary DC resistance [mΩ]")
    secondary_Rac_Rdc: float = Field(default=1.0, ge=1.0, description="AC/DC resistance ratio")
    
    # Window utilization
    total_Ku: float = Field(..., ge=0, le=1, description="Total window utilization")
    Ku_status: Literal["ok", "warning", "error"] = Field(..., description="Window fill status")


class LossAnalysis(BaseModel):
    """Loss breakdown"""
    
    # Core losses
    core_loss_W: float = Field(..., ge=0, description="Core loss [W]")
    core_loss_density_mW_cm3: float = Field(..., ge=0, description="Core loss density [mW/cm³]")
    
    # Copper losses
    primary_copper_loss_W: float = Field(..., ge=0, description="Primary copper loss [W]")
    secondary_copper_loss_W: float = Field(..., ge=0, description="Secondary copper loss [W]")
    total_copper_loss_W: float = Field(..., ge=0, description="Total copper loss [W]")
    
    # Totals
    total_loss_W: float = Field(..., ge=0, description="Total power loss [W]")
    efficiency_percent: float = Field(..., ge=0, le=100, description="Calculated efficiency [%]")
    
    # Loss ratio
    Pfe_Pcu_ratio: float = Field(..., ge=0, description="Core/copper loss ratio")


class ThermalAnalysis(BaseModel):
    """Thermal analysis results"""
    
    power_dissipation_density_W_cm2: float = Field(..., ge=0, description="Power dissipation density ψ [W/cm²]")
    temperature_rise_C: float = Field(..., ge=0, description="Estimated temperature rise [°C]")
    hotspot_temp_C: float = Field(..., ge=0, description="Estimated hotspot temperature [°C]")
    
    thermal_margin_C: float = Field(..., description="Margin to max temperature [°C]")
    thermal_status: Literal["pass", "warning", "fail"] = Field(..., description="Thermal status")
    
    cooling_recommendation: str = Field(..., description="Cooling recommendation")


class VerificationStatus(BaseModel):
    """Design verification checklist"""
    
    electrical: Literal["pass", "warning", "fail"] = Field(..., description="Electrical verification")
    mechanical: Literal["pass", "warning", "fail"] = Field(..., description="Mechanical verification")
    thermal: Literal["pass", "warning", "fail"] = Field(..., description="Thermal verification")
    
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    recommendations: List[str] = Field(default_factory=list, description="Design recommendations")


class TransformerDesignResult(BaseModel):
    """Complete transformer design output"""
    
    # Design method used
    design_method: str = Field(..., description="Design method used (Ap, Kg, Kgfe)")
    design_method_name: str = Field(default="McLyman Ap", description="Human-readable method name")
    calculated_Ap_cm4: float = Field(..., ge=0, description="Calculated area product [cm⁴]")
    calculated_Kg_cm5: Optional[float] = Field(default=None, description="Calculated core geometry [cm⁵]")
    optimal_Pfe_Pcu_ratio: Optional[float] = Field(default=None, description="Optimal loss ratio (Erickson)")
    
    # Selected core
    core: CoreSelection
    
    # Alternative cores that also meet requirements
    alternative_cores: List[dict] = Field(default_factory=list, description="Other viable cores")
    
    # Winding design
    winding: WindingDesign
    
    # Electrical parameters
    turns_ratio: float = Field(..., gt=0, description="Actual turns ratio")
    magnetizing_inductance_uH: Optional[float] = Field(default=None, description="Magnetizing inductance [μH]")
    leakage_inductance_uH: Optional[float] = Field(default=None, description="Estimated leakage inductance [μH]")
    
    # Analysis results
    losses: LossAnalysis
    thermal: ThermalAnalysis
    verification: VerificationStatus
    
    # Summary
    design_viable: bool = Field(..., description="Is the design viable?")
    confidence_score: float = Field(..., ge=0, le=1, description="Design confidence score")


class DesignSuggestion(BaseModel):
    """A design modification suggestion"""
    
    parameter: str = Field(..., description="Parameter to modify")
    current_value: float = Field(..., description="Current value")
    suggested_value: float = Field(..., description="Suggested value")
    unit: str = Field(default="", description="Unit of measurement")
    impact: str = Field(..., description="Expected impact of change")
    feasible: bool = Field(default=True, description="Is this suggestion feasible?")


class CoreAlternative(BaseModel):
    """Alternative core suggestion"""
    
    part_number: str
    manufacturer: str
    geometry: str
    Ap_cm4: float
    max_power_W: float = Field(..., description="Max power this core can handle at given frequency")
    notes: str = Field(default="", description="Additional notes")


class NoMatchResult(BaseModel):
    """Result when no suitable core is found - provides suggestions instead of error"""
    
    success: bool = Field(default=False)
    message: str = Field(..., description="Explanation of why no core was found")
    
    # What was requested
    required_Ap_cm4: float = Field(..., description="Required Area Product")
    available_max_Ap_cm4: float = Field(..., description="Largest available Ap in database")
    
    # Suggestions to make design feasible
    suggestions: List[DesignSuggestion] = Field(default_factory=list)
    
    # Closest available cores
    closest_cores: List[CoreAlternative] = Field(default_factory=list)
    
    # Alternative approaches
    alternative_approaches: List[str] = Field(default_factory=list)

