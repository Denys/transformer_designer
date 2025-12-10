"""
Pydantic models for pulse transformer design

Pulse transformers are used for:
- Gate drive circuits (IGBTs, MOSFETs, thyristors)
- Signal isolation
- Trigger circuits
- High-voltage pulse generation

Key parameters differ from power transformers:
- Volt-second rating (V·µs) instead of steady-state power
- Rise/fall time requirements
- Pulse width and duty cycle
- Droop and backswing specifications
- High-voltage isolation per IEC 60664
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class PulseApplicationType(str, Enum):
    """Pulse transformer application types."""
    GATE_DRIVE = "gate_drive"
    SIGNAL_ISOLATION = "signal_isolation"
    TRIGGER = "trigger"
    HV_PULSE = "hv_pulse"
    HV_POWER_PULSE = "hv_power_pulse"  # High-voltage high-current energy transfer (like Dropless)
    ETHERNET = "ethernet"
    TELECOM = "telecom"
    CUSTOM = "custom"


class InsulationType(str, Enum):
    """Insulation type per IEC 60664."""
    FUNCTIONAL = "functional"
    BASIC = "basic"
    SUPPLEMENTARY = "supplementary"
    DOUBLE = "double"
    REINFORCED = "reinforced"


class OvervoltageCategory(str, Enum):
    """Overvoltage category per IEC 60664."""
    CAT_I = "I"      # Equipment connected to circuits with transient overvoltage limited
    CAT_II = "II"    # Equipment connected to the fixed installation (plug-in)
    CAT_III = "III"  # Equipment in fixed installations, distribution level
    CAT_IV = "IV"    # Equipment at origin of installation (utility)


class PollutionDegree(int, Enum):
    """Pollution degree per IEC 60664."""
    PD1 = 1  # No pollution or only dry, non-conductive pollution
    PD2 = 2  # Normally only non-conductive pollution, occasional condensation
    PD3 = 3  # Conductive pollution or dry non-conductive becoming conductive due to condensation


class CoreMaterialType(str, Enum):
    """Core material type for pulse transformers."""
    FERRITE = "ferrite"              # For HF gate-drive (f > 10kHz, Bmax ~0.2-0.35T)
    SILICON_STEEL = "silicon_steel"  # For LF power pulse (f < 1kHz, Bmax ~1.2-1.5T)
    AMORPHOUS = "amorphous"          # Medium frequency (Bmax ~1.0-1.2T)
    NANOCRYSTALLINE = "nanocrystalline"  # Wide frequency range (Bmax ~0.8-1.0T)


# ============================================================================
# Request Models
# ============================================================================

class PulseTransformerRequirements(BaseModel):
    """Input requirements for pulse transformer design."""
    
    # Application
    application: PulseApplicationType = Field(
        PulseApplicationType.GATE_DRIVE,
        description="Pulse transformer application type"
    )
    
    # Voltage specifications
    primary_voltage_V: float = Field(
        ...,
        gt=0,
        description="Primary pulse voltage [V]"
    )
    secondary_voltage_V: float = Field(
        ...,
        gt=0,
        description="Secondary pulse voltage [V]"
    )
    
    # Pulse specifications
    pulse_width_us: float = Field(
        ...,
        gt=0,
        description="Pulse width [µs]"
    )
    rise_time_ns: Optional[float] = Field(
        None,
        gt=0,
        description="Required rise time [ns]"
    )
    fall_time_ns: Optional[float] = Field(
        None,
        gt=0,
        description="Required fall time [ns]"
    )
    duty_cycle_percent: float = Field(
        50.0,
        ge=0.1,
        le=99,
        description="Duty cycle [%]"
    )
    frequency_Hz: float = Field(
        ...,
        gt=0,
        description="Switching frequency [Hz]"
    )
    
    # Load specifications
    load_resistance_ohm: Optional[float] = Field(
        None,
        gt=0,
        description="Load resistance [Ω]"
    )
    load_capacitance_pF: Optional[float] = Field(
        None,
        ge=0,
        description="Load capacitance [pF]"
    )
    peak_current_A: Optional[float] = Field(
        None,
        gt=0,
        description="Peak current [A] - for HV/HC pulse applications"
    )
    
    # Energy-mode parameters (for HV_POWER_PULSE like Dropless)
    primary_capacitance_uF: Optional[float] = Field(
        None,
        gt=0,
        description="Primary discharge capacitance [µF] - for capacitor discharge mode"
    )
    secondary_capacitance_uF: Optional[float] = Field(
        None,
        gt=0,
        description="Secondary load capacitance [µF] - for energy transfer mode"
    )
    energy_per_pulse_J: Optional[float] = Field(
        None,
        gt=0,
        description="Required energy per pulse [J]"
    )
    pulse_width_ms: Optional[float] = Field(
        None,
        gt=0,
        description="Pulse width [ms] - for millisecond-range pulses"
    )
    
    # Performance requirements
    max_droop_percent: float = Field(
        10.0,
        gt=0,
        le=50,
        description="Maximum pulse top droop [%]"
    )
    max_backswing_percent: float = Field(
        20.0,
        gt=0,
        le=100,
        description="Maximum backswing voltage [%]"
    )
    
    # Isolation requirements
    isolation_voltage_Vrms: float = Field(
        1500.0,
        gt=0,
        description="Required isolation voltage [Vrms]"
    )
    insulation_type: InsulationType = Field(
        InsulationType.BASIC,
        description="Insulation type per IEC 60664"
    )
    overvoltage_category: OvervoltageCategory = Field(
        OvervoltageCategory.CAT_II,
        description="Overvoltage category"
    )
    pollution_degree: PollutionDegree = Field(
        PollutionDegree.PD2,
        description="Pollution degree"
    )
    
    # Thermal
    ambient_temp_C: float = Field(
        25.0,
        description="Ambient temperature [°C]"
    )
    max_temp_rise_C: float = Field(
        40.0,
        gt=0,
        description="Maximum temperature rise [°C]"
    )
    
    # Design preferences
    preferred_core_geometry: Optional[str] = Field(
        None,
        description="Preferred core geometry (RM, EFD, EI, toroid, etc.)"
    )
    preferred_material: Optional[str] = Field(
        None,
        description="Preferred core material grade (N87, M6, etc.)"
    )
    core_material_type: Optional[CoreMaterialType] = Field(
        None,
        description="Core material type (auto-selected based on frequency if not specified)"
    )
    max_height_mm: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum height constraint [mm]"
    )
    max_footprint_mm2: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum PCB footprint [mm²]"
    )
    
    # For HV power pulse: specify turns directly
    primary_turns: Optional[int] = Field(
        None,
        ge=1,
        description="Fixed primary turns (for HV_POWER_PULSE if specified)"
    )
    secondary_turns: Optional[int] = Field(
        None,
        ge=1,
        description="Fixed secondary turns (for HV_POWER_PULSE if specified)"
    )


class InsulationCalculationRequest(BaseModel):
    """Request for IEC 60664 insulation calculation."""
    
    working_voltage_Vrms: float = Field(
        ...,
        gt=0,
        description="Working voltage [Vrms]"
    )
    insulation_type: InsulationType = Field(
        InsulationType.BASIC,
        description="Required insulation type"
    )
    overvoltage_category: OvervoltageCategory = Field(
        OvervoltageCategory.CAT_II,
        description="Overvoltage category"
    )
    pollution_degree: PollutionDegree = Field(
        PollutionDegree.PD2,
        description="Pollution degree"
    )
    altitude_m: float = Field(
        2000.0,
        ge=0,
        description="Installation altitude [m]"
    )
    material_group: Literal["I", "II", "IIIa", "IIIb"] = Field(
        "II",
        description="Insulation material group"
    )


# ============================================================================
# Analysis/Result Models
# ============================================================================

class VoltSecondResult(BaseModel):
    """Volt-second calculation result."""
    volt_second_uVs: float = Field(..., description="Volt-second product [V·µs]")
    volt_second_mVs: float = Field(..., description="Volt-second product [mV·s]")
    required_core_Ae_cm2: float = Field(..., description="Minimum core area [cm²]")
    required_core_Ae_mm2: float = Field(..., description="Minimum core area [mm²]")
    Bmax_T: float = Field(..., description="Maximum flux density [T]")
    primary_turns_min: int = Field(..., description="Minimum primary turns")


class PulseResponseAnalysis(BaseModel):
    """Pulse waveform analysis results."""
    calculated_rise_time_ns: float = Field(..., description="Calculated rise time [ns]")
    calculated_fall_time_ns: float = Field(..., description="Calculated fall time [ns]")
    pulse_droop_percent: float = Field(..., description="Calculated pulse droop [%]")
    backswing_percent: float = Field(..., description="Calculated backswing [%]")
    ringing_frequency_MHz: Optional[float] = Field(None, description="Ringing frequency [MHz]")
    bandwidth_3dB_MHz: float = Field(..., description="-3dB bandwidth [MHz]")
    meets_rise_time_spec: bool = Field(..., description="Meets rise time requirement")
    meets_droop_spec: bool = Field(..., description="Meets droop requirement")


class InsulationResult(BaseModel):
    """IEC 60664 insulation calculation result."""
    
    # Clearance (through air)
    required_clearance_mm: float = Field(..., description="Required clearance [mm]")
    
    # Creepage (over surface)
    required_creepage_mm: float = Field(..., description="Required creepage [mm]")
    
    # Solid insulation
    required_solid_insulation_mm: float = Field(..., description="Required solid insulation thickness [mm]")
    
    # Withstand voltages
    impulse_withstand_kV: float = Field(..., description="Impulse withstand voltage [kV]")
    ac_withstand_Vrms: float = Field(..., description="AC withstand voltage [Vrms]")
    
    # Design recommendations
    recommended_wire_insulation: str = Field(..., description="Recommended wire insulation type")
    recommended_interlayer_mm: float = Field(..., description="Recommended interlayer insulation [mm]")
    construction_notes: List[str] = Field(default_factory=list, description="Construction notes")


class PulseTransformerWinding(BaseModel):
    """Pulse transformer winding design."""
    turns: int = Field(..., description="Number of turns")
    wire_type: str = Field(..., description="Wire type (solid, litz, foil)")
    wire_awg: Optional[int] = Field(None, description="Wire AWG (for solid/litz)")
    wire_thickness_mm: Optional[float] = Field(None, description="Wire thickness (for foil)")
    wire_width_mm: Optional[float] = Field(None, description="Wire width (for foil)")
    layers: int = Field(..., description="Number of layers")
    Rdc_mOhm: float = Field(..., description="DC resistance [mΩ]")
    Rac_factor: float = Field(..., description="AC/DC resistance ratio")
    inductance_uH: float = Field(..., description="Winding inductance [µH]")
    capacitance_pF: float = Field(..., description="Winding capacitance [pF]")


class PulseTransformerDesignResult(BaseModel):
    """Complete pulse transformer design result."""
    
    # Input summary
    application: PulseApplicationType
    volt_second_uVs: float = Field(..., description="Volt-second rating [V·µs]")
    turns_ratio: float
    
    # Core selection
    core_part_number: str
    core_manufacturer: str
    core_geometry: str
    core_material: str
    core_Ae_cm2: float
    core_Ap_cm4: float
    core_source: str = "local"
    
    # Winding design
    primary: PulseTransformerWinding
    secondary: PulseTransformerWinding
    
    # Electrical parameters
    magnetizing_inductance_uH: float = Field(..., description="Magnetizing inductance [µH]")
    leakage_inductance_nH: float = Field(..., description="Leakage inductance [nH]")
    interwinding_capacitance_pF: float = Field(..., description="Interwinding capacitance [pF]")
    
    # Pulse response
    pulse_response: PulseResponseAnalysis
    
    # Insulation
    insulation: InsulationResult
    
    # Thermal
    core_loss_mW: float = Field(..., description="Core loss [mW]")
    copper_loss_mW: float = Field(..., description="Copper loss [mW]")
    total_loss_mW: float = Field(..., description="Total loss [mW]")
    temperature_rise_C: float = Field(..., description="Temperature rise [°C]")
    
    # Verification
    meets_specifications: bool
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# Simplified Gate Driver Preset
# ============================================================================

class GateDriverPreset(BaseModel):
    """Preset configurations for common gate driver applications."""
    
    name: str
    description: str
    device_type: Literal["MOSFET", "IGBT", "SiC_MOSFET", "GaN_HEMT", "Thyristor"]
    
    # Typical requirements
    typical_Vdrive: float  # Gate drive voltage
    typical_Ipeak: float   # Peak gate current
    typical_Qg_nC: float   # Gate charge
    typical_ton_ns: float  # Turn-on time requirement
    typical_toff_ns: float # Turn-off time requirement
    
    # Suggested specs
    suggested_turns_ratio: float = 1.0
    suggested_Lm_min_uH: float = 100.0
    suggested_Llk_max_nH: float = 50.0


# Pre-defined gate driver presets
GATE_DRIVER_PRESETS = {
    "mosfet_100v": GateDriverPreset(
        name="MOSFET 100V Class",
        description="Low voltage MOSFETs (≤100V)",
        device_type="MOSFET",
        typical_Vdrive=12.0,
        typical_Ipeak=2.0,
        typical_Qg_nC=50,
        typical_ton_ns=50,
        typical_toff_ns=50,
        suggested_turns_ratio=1.0,
        suggested_Lm_min_uH=50,
        suggested_Llk_max_nH=30,
    ),
    "mosfet_600v": GateDriverPreset(
        name="MOSFET 600V Class",
        description="High voltage MOSFETs (≤600V)",
        device_type="MOSFET",
        typical_Vdrive=15.0,
        typical_Ipeak=4.0,
        typical_Qg_nC=100,
        typical_ton_ns=100,
        typical_toff_ns=100,
        suggested_turns_ratio=1.0,
        suggested_Lm_min_uH=100,
        suggested_Llk_max_nH=50,
    ),
    "igbt_standard": GateDriverPreset(
        name="IGBT Standard",
        description="Standard IGBTs",
        device_type="IGBT",
        typical_Vdrive=15.0,
        typical_Ipeak=5.0,
        typical_Qg_nC=500,
        typical_ton_ns=200,
        typical_toff_ns=300,
        suggested_turns_ratio=1.0,
        suggested_Lm_min_uH=200,
        suggested_Llk_max_nH=100,
    ),
    "sic_mosfet": GateDriverPreset(
        name="SiC MOSFET",
        description="Silicon Carbide MOSFETs",
        device_type="SiC_MOSFET",
        typical_Vdrive=20.0,
        typical_Ipeak=6.0,
        typical_Qg_nC=80,
        typical_ton_ns=30,
        typical_toff_ns=30,
        suggested_turns_ratio=1.0,
        suggested_Lm_min_uH=50,
        suggested_Llk_max_nH=20,
    ),
    "gan_hemt": GateDriverPreset(
        name="GaN HEMT",
        description="Gallium Nitride HEMTs",
        device_type="GaN_HEMT",
        typical_Vdrive=6.0,
        typical_Ipeak=3.0,
        typical_Qg_nC=10,
        typical_ton_ns=10,
        typical_toff_ns=10,
        suggested_turns_ratio=1.0,
        suggested_Lm_min_uH=30,
        suggested_Llk_max_nH=10,
    ),
}