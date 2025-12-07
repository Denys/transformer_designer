"""
MAS (Magnetic Agnostic Structure) Exporter

Exports transformer/inductor designs to the OpenMagnetics MAS JSON format
for interoperability with FEA tools (FEMM, COMSOL, Ansys) and other
magnetic design software.

MAS Specification: https://github.com/OpenMagnetics/MAS
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import math


# ============================================================================
# MAS Data Structures
# ============================================================================

@dataclass
class MASInputs:
    """MAS inputs section - design requirements."""
    designRequirements: Dict[str, Any] = field(default_factory=dict)
    operatingPoints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MASMagneticCore:
    """MAS magnetic core definition."""
    name: str
    functionalDescription: Dict[str, Any] = field(default_factory=dict)
    geometricalDescription: Optional[Dict[str, Any]] = None
    processedDescription: Optional[Dict[str, Any]] = None
    manufacturerInfo: Optional[Dict[str, Any]] = None


@dataclass
class MASCoilFunctionalDescription:
    """MAS coil functional description."""
    name: str
    numberTurns: int
    numberParallels: int
    isolationSide: str = "primary"
    wire: Optional[Dict[str, Any]] = None


@dataclass
class MASCoil:
    """MAS coil/winding definition."""
    bobbin: Optional[str] = None
    functionalDescription: List[MASCoilFunctionalDescription] = field(default_factory=list)
    turnsDescription: Optional[List[Dict[str, Any]]] = None


@dataclass
class MASMagnetic:
    """MAS magnetic component."""
    core: MASMagneticCore = field(default_factory=lambda: MASMagneticCore(name=""))
    coil: MASCoil = field(default_factory=MASCoil)


@dataclass
class MASOutputs:
    """MAS outputs section - calculated results."""
    coreLosses: Optional[Dict[str, Any]] = None
    windingLosses: Optional[Dict[str, Any]] = None
    temperature: Optional[Dict[str, Any]] = None
    leakageInductance: Optional[Dict[str, Any]] = None
    magnetizingInductance: Optional[Dict[str, Any]] = None


@dataclass
class MASDocument:
    """Complete MAS document structure."""
    inputs: MASInputs
    magnetic: MASMagnetic
    outputs: Optional[MASOutputs] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Wire Type Mappings
# ============================================================================

AWG_TO_DIAMETER_MM = {
    10: 2.588, 11: 2.305, 12: 2.053, 13: 1.828, 14: 1.628,
    15: 1.450, 16: 1.291, 17: 1.150, 18: 1.024, 19: 0.912,
    20: 0.812, 21: 0.723, 22: 0.644, 23: 0.573, 24: 0.511,
    25: 0.455, 26: 0.405, 27: 0.361, 28: 0.321, 29: 0.286,
    30: 0.255, 31: 0.227, 32: 0.202, 33: 0.180, 34: 0.160,
    35: 0.143, 36: 0.127, 37: 0.113, 38: 0.101, 39: 0.090,
    40: 0.080, 41: 0.071, 42: 0.064, 43: 0.056, 44: 0.051,
}


# ============================================================================
# MAS Exporter Class
# ============================================================================

class MASExporter:
    """
    Exports transformer designs to MAS JSON format.
    
    Handles:
    - Core geometry with all dimensional parameters
    - Winding definitions with wire specifications
    - Operating points (voltage, current, frequency)
    - Loss calculations and thermal results
    """
    
    MAS_VERSION = "0.9.0"
    TOOL_NAME = "TransformerDesigner"
    TOOL_VERSION = "1.0.0"
    
    def __init__(self):
        """Initialize the MAS exporter."""
        pass
    
    def export_transformer(
        self,
        design_result: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Export a transformer design to MAS format.
        
        Args:
            design_result: Complete transformer design result
            requirements: Original design requirements
            
        Returns:
            MAS-formatted dictionary
        """
        # Create MAS document structure
        mas_doc = {
            "$schema": "https://openmagnetics.github.io/MAS/schemas/MAS.json",
            "version": self.MAS_VERSION,
            "inputs": self._build_inputs(requirements, design_result),
            "magnetic": self._build_magnetic(design_result, requirements),
            "outputs": self._build_outputs(design_result),
            "metadata": self._build_metadata(),
        }
        
        return mas_doc
    
    def export_to_json(
        self,
        design_result: Dict[str, Any],
        requirements: Dict[str, Any],
        pretty: bool = True,
    ) -> str:
        """
        Export transformer design to MAS JSON string.
        
        Args:
            design_result: Complete transformer design result
            requirements: Original design requirements
            pretty: Whether to format JSON with indentation
            
        Returns:
            JSON string in MAS format
        """
        mas_doc = self.export_transformer(design_result, requirements)
        
        if pretty:
            return json.dumps(mas_doc, indent=2, ensure_ascii=False)
        else:
            return json.dumps(mas_doc, ensure_ascii=False)
    
    def _build_inputs(
        self,
        requirements: Dict[str, Any],
        design_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build MAS inputs section."""
        
        # Design requirements
        design_reqs = {
            "name": requirements.get('name', 'Transformer Design'),
            "turnsRatioRange": {
                "minimum": design_result.get('turns_ratio', 1) * 0.95,
                "nominal": design_result.get('turns_ratio', 1),
                "maximum": design_result.get('turns_ratio', 1) * 1.05,
            },
            "isolation": {
                "type": "functional",  # or "reinforced" for HV
            },
            "insulationRequirements": {
                "pollutionDegree": 2,
                "overvoltageCategory": "II",
            },
        }
        
        # Operating point
        Vp = requirements.get('primary_voltage_V', 0)
        Vs = requirements.get('secondary_voltage_V', 0)
        Pout = requirements.get('output_power_W', 0)
        freq = requirements.get('frequency_Hz', 0)
        waveform = requirements.get('waveform', 'sinusoidal')
        duty_cycle = requirements.get('duty_cycle', 0.5)
        
        # Calculate currents
        efficiency = requirements.get('efficiency_percent', 95) / 100
        Is = Pout / Vs if Vs > 0 else 0
        Ip = Pout / (Vp * efficiency) if Vp > 0 else 0
        
        operating_point = {
            "name": "Primary Operating Point",
            "conditions": {
                "ambientTemperature": requirements.get('ambient_temp_C', 25),
                "cooling": requirements.get('cooling', 'natural'),
            },
            "excitationsPerWinding": [
                {
                    "frequency": freq,
                    "current": {
                        "waveform": {
                            "data": self._generate_waveform_data(Ip, waveform, duty_cycle),
                        },
                        "processed": {
                            "rms": Ip,
                            "peak": Ip * (math.sqrt(2) if waveform == 'sinusoidal' else 1),
                        },
                    },
                    "voltage": {
                        "waveform": {
                            "data": self._generate_waveform_data(Vp, waveform, duty_cycle),
                        },
                        "processed": {
                            "rms": Vp,
                            "peak": Vp * (math.sqrt(2) if waveform == 'sinusoidal' else 1),
                        },
                    },
                },
                {
                    "frequency": freq,
                    "current": {
                        "processed": {
                            "rms": Is,
                            "peak": Is * (math.sqrt(2) if waveform == 'sinusoidal' else 1),
                        },
                    },
                    "voltage": {
                        "processed": {
                            "rms": Vs,
                            "peak": Vs * (math.sqrt(2) if waveform == 'sinusoidal' else 1),
                        },
                    },
                },
            ],
        }
        
        return {
            "designRequirements": design_reqs,
            "operatingPoints": [operating_point],
        }
    
    def _build_magnetic(
        self,
        design_result: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build MAS magnetic (core + coil) section."""
        
        core_data = design_result.get('core', {})
        winding_data = design_result.get('winding', {})
        
        # Core section
        core = {
            "name": core_data.get('part_number', 'Unknown'),
            "functionalDescription": {
                "type": "two-piece set",
                "material": core_data.get('material', 'N87'),
                "shape": self._get_shape_info(core_data),
                "gapping": [],  # No gap for transformer
            },
            "geometricalDescription": self._build_core_geometry(core_data),
            "processedDescription": {
                "effectiveParameters": {
                    "effectiveArea": core_data.get('Ae_cm2', 0) * 1e-4,  # cm² to m²
                    "effectiveLength": core_data.get('lm_cm', 0) * 1e-2,  # cm to m
                    "effectiveVolume": core_data.get('Ve_cm3', 0) * 1e-6, # cm³ to m³
                    "minimumArea": core_data.get('Ae_cm2', 0) * 1e-4 * 0.95,
                },
                "windingWindows": [
                    {
                        "area": core_data.get('Wa_cm2', 0) * 1e-4,  # cm² to m²
                        "width": math.sqrt(core_data.get('Wa_cm2', 0)) * 1e-2 * 0.8,
                        "height": math.sqrt(core_data.get('Wa_cm2', 0)) * 1e-2 * 1.2,
                    }
                ],
            },
            "manufacturerInfo": {
                "name": core_data.get('manufacturer', ''),
                "reference": core_data.get('part_number', ''),
                "datasheetUrl": core_data.get('datasheet_url', ''),
            },
        }
        
        # Coil/Winding section
        coil = {
            "functionalDescription": [
                {
                    "name": "Primary",
                    "numberTurns": winding_data.get('primary_turns', 0),
                    "numberParallels": winding_data.get('primary_strands', 1),
                    "isolationSide": "primary",
                    "wire": self._build_wire_spec(
                        winding_data.get('primary_wire_awg', 20),
                        winding_data.get('primary_wire_dia_mm', 0.8),
                        winding_data.get('primary_strands', 1),
                        winding_data.get('primary_wire_type', 'solid'),
                    ),
                },
                {
                    "name": "Secondary",
                    "numberTurns": winding_data.get('secondary_turns', 0),
                    "numberParallels": winding_data.get('secondary_strands', 1),
                    "isolationSide": "secondary",
                    "wire": self._build_wire_spec(
                        winding_data.get('secondary_wire_awg', 18),
                        winding_data.get('secondary_wire_dia_mm', 1.0),
                        winding_data.get('secondary_strands', 1),
                        winding_data.get('secondary_wire_type', 'solid'),
                    ),
                },
            ],
            "layersDescription": self._build_layers_description(winding_data),
        }
        
        return {
            "core": core,
            "coil": coil,
        }
    
    def _build_outputs(self, design_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build MAS outputs section with calculated results."""
        
        losses = design_result.get('losses', {})
        thermal = design_result.get('thermal', {})
        
        return {
            "coreLosses": {
                "origin": "calculated",
                "method": design_result.get('design_method', 'steinmetz'),
                "losses": [
                    {
                        "lossDensity": losses.get('core_loss_density_mW_cm3', 0) * 1000,  # to W/m³
                        "loss": losses.get('core_loss_W', 0),
                    }
                ],
            },
            "windingLosses": {
                "origin": "calculated",
                "losses": [
                    {
                        "name": "Primary",
                        "dcLoss": losses.get('primary_copper_loss_W', 0) * 0.7,  # Estimate DC portion
                        "acLoss": losses.get('primary_copper_loss_W', 0) * 0.3,  # Estimate AC portion
                        "totalLoss": losses.get('primary_copper_loss_W', 0),
                    },
                    {
                        "name": "Secondary",
                        "dcLoss": losses.get('secondary_copper_loss_W', 0) * 0.7,
                        "acLoss": losses.get('secondary_copper_loss_W', 0) * 0.3,
                        "totalLoss": losses.get('secondary_copper_loss_W', 0),
                    },
                ],
            },
            "temperature": {
                "origin": "calculated",
                "method": "mclyman_empirical",
                "surfaceTemperature": {
                    "maximum": thermal.get('hotspot_temp_C', 100),
                },
                "temperatureRise": thermal.get('temperature_rise_C', 40),
            },
            "magnetizingInductance": {
                "origin": "calculated",
                "inductance": design_result.get('magnetizing_inductance_uH', 0) * 1e-6,  # uH to H
            },
            "leakageInductance": {
                "origin": "calculated", 
                "inductance": design_result.get('leakage_inductance_uH', 0) * 1e-6,
            },
            "efficiency": {
                "percent": losses.get('efficiency_percent', 95),
                "totalLoss": losses.get('total_loss_W', 0),
            },
        }
    
    def _build_metadata(self) -> Dict[str, Any]:
        """Build MAS metadata section."""
        return {
            "uuid": str(uuid.uuid4()),
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "tool": {
                "name": self.TOOL_NAME,
                "version": self.TOOL_VERSION,
            },
            "notes": "Generated by Transformer Designer - McLyman/Erickson methodology",
        }
    
    def _get_shape_info(self, core_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get MAS shape information from core data."""
        geometry = core_data.get('geometry', 'E').upper()
        
        # Map our geometry names to MAS family names
        shape_families = {
            'E': 'e', 'EE': 'e', 'EI': 'ei',
            'ETD': 'etd', 'ER': 'er', 'EQ': 'eq',
            'PQ': 'pq', 'PM': 'pm', 'P': 'p',
            'RM': 'rm', 'POT': 'pot',
            'T': 't', 'TOROID': 't',
            'U': 'u', 'UI': 'ui', 'UU': 'uu',
        }
        
        family = shape_families.get(geometry, 'e')
        
        return {
            "family": family,
            "name": core_data.get('part_number', 'Unknown'),
        }
    
    def _build_core_geometry(self, core_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build geometrical description from core data."""
        
        # Estimate dimensions from area product
        Ap_cm4 = core_data.get('Ap_cm4', 1)
        Ae_cm2 = core_data.get('Ae_cm2', 1)
        Wa_cm2 = core_data.get('Wa_cm2', 1)
        
        # Estimate outer dimensions
        # For E-type cores, approximate: width ≈ 3 * sqrt(Ae)
        center_leg_width = math.sqrt(Ae_cm2) * 1e-2  # cm to m
        width = center_leg_width * 3
        depth = center_leg_width * 1.2
        height = math.sqrt(Wa_cm2) * 1e-2 * 1.5
        
        return {
            "type": "half-set",
            "dimensions": {
                "A": width,  # Overall width
                "B": height,  # Overall height  
                "C": depth,  # Overall depth
            },
        }
    
    def _build_wire_spec(
        self,
        awg: int,
        diameter_mm: float,
        strands: int,
        wire_type: str,
    ) -> Dict[str, Any]:
        """Build MAS wire specification."""
        
        if wire_type == 'litz':
            return {
                "type": "litz",
                "strand": {
                    "type": "round",
                    "conductingDiameter": diameter_mm / strands * 1e-3,  # mm to m
                    "material": "copper",
                },
                "numberConductors": strands,
                "outerDiameter": diameter_mm * 1e-3,
            }
        else:
            return {
                "type": "round",
                "conductingDiameter": diameter_mm * 1e-3,  # mm to m
                "material": "copper",
                "coating": {
                    "type": "enameled",
                    "temperatureRating": 180,  # Class H
                },
                "standard": f"AWG {awg}" if awg else None,
            }
    
    def _build_layers_description(
        self,
        winding_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build winding layers description."""
        
        layers = []
        
        # Primary layers
        primary_layers = winding_data.get('primary_layers', 1)
        for i in range(primary_layers):
            layers.append({
                "type": "conduction", 
                "winding": "Primary",
                "orientation": "horizontal",
            })
        
        # Insulation between primary and secondary
        layers.append({
            "type": "insulation",
            "material": "polyimide",
            "thickness": 0.05e-3,  # 50 µm typical
        })
        
        # Secondary layers
        secondary_layers = winding_data.get('secondary_layers', 1)
        for i in range(secondary_layers):
            layers.append({
                "type": "conduction",
                "winding": "Secondary", 
                "orientation": "horizontal",
            })
        
        return layers
    
    def _generate_waveform_data(
        self,
        amplitude: float,
        waveform: str,
        duty_cycle: float = 0.5,
    ) -> List[Dict[str, float]]:
        """Generate waveform data points for MAS."""
        
        if waveform == 'sinusoidal':
            # 8 points for sine wave
            points = []
            for i in range(8):
                t = i / 8
                v = amplitude * math.sqrt(2) * math.sin(2 * math.pi * t)
                points.append({"time": t, "value": v})
            return points
            
        elif waveform == 'square':
            return [
                {"time": 0, "value": amplitude},
                {"time": duty_cycle - 0.001, "value": amplitude},
                {"time": duty_cycle, "value": -amplitude},
                {"time": 1 - 0.001, "value": -amplitude},
                {"time": 1, "value": amplitude},
            ]
            
        elif waveform == 'triangular':
            return [
                {"time": 0, "value": 0},
                {"time": 0.25, "value": amplitude},
                {"time": 0.5, "value": 0},
                {"time": 0.75, "value": -amplitude},
                {"time": 1, "value": 0},
            ]
        
        else:
            # Default to DC
            return [
                {"time": 0, "value": amplitude},
                {"time": 1, "value": amplitude},
            ]


# ============================================================================
# FEMM Export Support
# ============================================================================

class FEMMExporter:
    """
    Export transformer designs to FEMM (Finite Element Method Magnetics) format.
    
    FEMM is a free 2D FEA tool for magnetics, electrostatics, heat flow, etc.
    https://www.femm.info
    """
    
    def __init__(self):
        pass
    
    def export_lua_script(
        self,
        design_result: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> str:
        """
        Generate FEMM Lua script for the transformer design.
        
        Args:
            design_result: Complete transformer design
            requirements: Design requirements
            
        Returns:
            Lua script string for FEMM
        """
        core = design_result.get('core', {})
        winding = design_result.get('winding', {})
        freq = requirements.get('frequency_Hz', 0)
        
        # Extract parameters
        Ae_cm2 = core.get('Ae_cm2', 1)
        Wa_cm2 = core.get('Wa_cm2', 1)
        material = core.get('material', 'N87')
        Np = winding.get('primary_turns', 0)
        Ns = winding.get('secondary_turns', 0)
        
        # Estimate core dimensions for 2D cross-section
        center_leg_mm = math.sqrt(Ae_cm2) * 10
        window_width_mm = math.sqrt(Wa_cm2) * 10 * 0.8
        window_height_mm = math.sqrt(Wa_cm2) * 10 * 1.2
        
        script = f'''-- FEMM Lua Script for Transformer Design
-- Generated by Transformer Designer

-- Create new magnetics problem
newdocument(0)
mi_probdef({freq}, "millimeters", "axi", 1e-8)

-- Define materials
mi_addmaterial("Air", 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
mi_addmaterial("{material}", 2000, 2000, 0, 0, 0, 0, 0, 0, 0, 0)
mi_addmaterial("Copper", 1, 1, 0, 0, 58e6, 0, 0, 0, 0, 0)

-- Core dimensions
center_leg = {center_leg_mm}
window_w = {window_width_mm}
window_h = {window_height_mm}

-- Draw E-core cross-section (simplified)
-- Center leg
mi_drawrectangle(0, -window_h/2, center_leg/2, window_h/2)

-- Top yoke
mi_drawrectangle(0, window_h/2, center_leg/2 + window_w, window_h/2 + center_leg/2)

-- Bottom yoke  
mi_drawrectangle(0, -window_h/2 - center_leg/2, center_leg/2 + window_w, -window_h/2)

-- Outer leg
mi_drawrectangle(center_leg/2 + window_w, -window_h/2, center_leg/2 + window_w + center_leg/2, window_h/2)

-- Label core region
mi_addblocklabel(center_leg/4, 0)
mi_selectlabel(center_leg/4, 0)
mi_setblockprop("{material}", 0, 1, "<None>", 0, 0, 0)
mi_clearselected()

-- Primary winding region
mi_drawrectangle(center_leg/2 + 1, -window_h/2 + 2, center_leg/2 + window_w/2 - 1, window_h/2 - 2)
mi_addblocklabel(center_leg/2 + window_w/4, 0)
mi_selectlabel(center_leg/2 + window_w/4, 0)
mi_setblockprop("Copper", 0, 1, "Primary", 0, 0, {Np})
mi_clearselected()

-- Secondary winding region
mi_drawrectangle(center_leg/2 + window_w/2 + 1, -window_h/2 + 2, center_leg/2 + window_w - 1, window_h/2 - 2)
mi_addblocklabel(center_leg/2 + 3*window_w/4, 0)
mi_selectlabel(center_leg/2 + 3*window_w/4, 0)
mi_setblockprop("Copper", 0, 1, "Secondary", 0, 0, {Ns})
mi_clearselected()

-- Air region
mi_addblocklabel(center_leg + window_w/2, window_h)
mi_selectlabel(center_leg + window_w/2, window_h)
mi_setblockprop("Air", 0, 1, "<None>", 0, 0, 0)
mi_clearselected()

-- Define circuits
mi_addcircprop("Primary", 1, 1)   -- 1A excitation
mi_addcircprop("Secondary", 0, 1) -- Open circuit

-- Create boundary
mi_makeABC()

-- Zoom to fit
mi_zoomnatural()

-- Save file
mi_saveas("transformer_design.fem")

-- Run analysis
mi_analyze()
mi_loadsolution()

-- Post-processing
print("Transformer Analysis Results")
print("============================")

-- Get inductance
L = mo_getcircuitproperties("Primary")
print(string.format("Primary Inductance: %.3f mH", L[2]*1000))

-- Get flux linkage
print(string.format("Flux Linkage: %.6f Wb", L[1]))
'''
        
        return script


# ============================================================================
# Factory Functions
# ============================================================================

def create_mas_exporter() -> MASExporter:
    """Create a new MAS exporter instance."""
    return MASExporter()


def create_femm_exporter() -> FEMMExporter:
    """Create a new FEMM exporter instance."""
    return FEMMExporter()


def export_design_to_mas(
    design_result: Dict[str, Any],
    requirements: Dict[str, Any],
) -> str:
    """
    Convenience function to export a design to MAS JSON.
    
    Args:
        design_result: Complete transformer design
        requirements: Design requirements
        
    Returns:
        MAS JSON string
    """
    exporter = MASExporter()
    return exporter.export_to_json(design_result, requirements)


def export_design_to_femm(
    design_result: Dict[str, Any],
    requirements: Dict[str, Any],
) -> str:
    """
    Convenience function to export a design to FEMM Lua script.
    
    Args:
        design_result: Complete transformer design
        requirements: Design requirements
        
    Returns:
        FEMM Lua script string
    """
    exporter = FEMMExporter()
    return exporter.export_lua_script(design_result, requirements)