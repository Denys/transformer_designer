# OpenMagnetics Integration Plan

## Feasibility Analysis and Implementation Strategy

 

---

 

## Executive Summary

 

**OpenMagnetics** is an open-source platform for magnetic component design that provides:

- 40+ validated physics models (core losses, winding losses, thermal, insulation)

- Comprehensive core/material databases (shapes, materials, bobbins, wire)

- Multi-language APIs: C++ (MKF), Python (PyMKF), JavaScript (WebLibMKF), C# (MKFNet)

- Standardized data format: MAS (Magnetic Agnostic Structure) using JSON Schema

- Integration with ANSYS, FreeCAD, LTspice, Ngspice, PSIM, PSPICE

 

### Feasibility Assessment: ✅ HIGH

 

| Criterion | Assessment | Notes |

|-----------|------------|-------|

| **API Availability** | ✅ Excellent | PyMKF Python bindings available |

| **Data Format** | ✅ Excellent | MAS JSON schema well-documented |

| **Model Coverage** | ✅ Good | Core losses, winding losses, thermal, insulation |

| **License** | ✅ MIT | Fully permissive for commercial use |

| **Active Development** | ✅ Active | Recent commits, IEEE publication 2024 |

| **Documentation** | ⚠️ Moderate | Code-level docs limited, requires exploration |

| **Pulse Transformer Support** | ⚠️ Partial | Designed for SMPS; pulse mode needs validation |

 

### Integration Recommendation

 

**Phase 1**: Use OpenMagnetics as **supplementary calculation engine** alongside our McLyman-based framework

- Leverage PyMKF for core/material database queries

- Use MAS format for design export/import interoperability

- Validate our calculations against OpenMagnetics models

 

**Phase 2**: Deeper integration for advanced features

- FEA model export via MVB (Magnetics Virtual Builder)

- Ansys Maxwell integration via MAS → PyAEDT workflow

 

---

 

## OpenMagnetics Architecture Overview

 

```

┌─────────────────────────────────────────────────────────────────┐

│                    OpenMagnetics Ecosystem                       │

├─────────────────────────────────────────────────────────────────┤

│                                                                  │

│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐            │

│  │    MAS      │   │    MKF      │   │    MVB      │            │

│  │ JSON Schema │──▶│ C++ Engine  │──▶│ 3D Builder  │            │

│  │             │   │             │   │             │            │

│  │ - Inputs    │   │ - simulate()│   │ - FreeCAD   │            │

│  │ - Magnetic  │   │ - design()  │   │ - ANSYS     │            │

│  │ - Outputs   │   │ - catalog() │   │ - Meshes    │            │

│  └─────────────┘   └──────┬──────┘   └─────────────┘            │

│                           │                                      │

│         ┌─────────────────┼─────────────────┐                   │

│         │                 │                 │                   │

│    ┌────▼────┐      ┌─────▼─────┐    ┌─────▼─────┐             │

│    │  PyMKF  │      │ WebLibMKF │    │  MKFNet   │             │

│    │ Python  │      │ JS/WASM   │    │   C#      │             │

│    └─────────┘      └───────────┘    └───────────┘             │

│                                                                  │

└─────────────────────────────────────────────────────────────────┘

```

 

---

 

## Key OpenMagnetics Capabilities

 

### 1. Core/Material Database

 

**Available via `PyMKF.get_available_cores()`:**

 

```python

import PyMKF

 

# Get all available cores

cores = PyMKF.get_available_cores()

 

for core in cores:

    ref = core["manufacturerInfo"]["reference"]

    Ae = core["processedDescription"]["columns"][0]["area"]  # m²

    Wa = core["processedDescription"]["windingWindows"][0]["area"]  # m²

    Ap = Ae * Wa * 1e8  # Convert to cm⁴

 

    if abs(Ap - target_Ap) / target_Ap < 0.05:  # Within 5%

        print(f"Core: {ref}, Ap: {Ap:.2f} cm⁴")

```

 

**Core Data Structure:**

```json

{

  "manufacturerInfo": {

    "reference": "ETD39",

    "manufacturer": "Ferroxcube"

  },

  "processedDescription": {

    "columns": [{"area": 0.000123}],  // Ae in m²

    "windingWindows": [{"area": 0.000234}],  // Wa in m²

    "depth": 0.039,

    "width": 0.039,

    "height": 0.028

  },

  "functionalDescription": {

    "material": "3C95",

    "shape": "ETD",

    "gapping": []

  }

}

```

 

### 2. Core Loss Models

 

**Available models in MKF:**

 

| Model | Method | Best For |

|-------|--------|----------|

| `STEINMETZ` | Basic Steinmetz equation | Sinusoidal, single frequency |

| `IGSE` | Improved Generalized Steinmetz | Non-sinusoidal waveforms |

| `MSE` | Modified Steinmetz | DC bias conditions |

| `NSE` | Natural Steinmetz Extension | Arbitrary waveforms |

| `BARG` | Barg model | High accuracy |

| `ROSHEN` | Roshen model | Temperature-dependent |

| `PROPRIETARY` | Manufacturer data | Magnetics, Micrometals |

 

**Priority order (automatic selection):**

1. iGSE (if applicable)

2. Proprietary manufacturer models

3. Loss Factor approach

4. Steinmetz equation

5. ROSHEN fallback

 

### 3. Winding Loss Models

 

**Skin Effect:**

- Round wire: ALBACH model

- Litz wire: ALBACH + strand proximity

- Rectangular/Planar: KUTKUT model

- Foil: Specialized foil model

 

**Proximity Effect:**

- FERREIRA (round wire)

- LAMMERANER (general)

- ALBACH (rectangular)

 

### 4. Insulation Coordination

 

OpenMagnetics implements **IEC standards** for:

- Creepage distance calculation

- Clearance (air gap) requirements

- Withstand voltage determination

- Distance through insulation

 

**Aligns with our CLAUDE.md requirements for HV insulation design.**

 

### 5. Thermal Models

 

- Core temperature estimation (Maniktala method)

- Surface dissipation calculations

- Temperature-dependent material properties

 

---

 

## MAS (Magnetic Agnostic Structure) Format

 

### Purpose

 

MAS provides a **standardized JSON format** for describing magnetic components that can be:

- Human-readable and editable

- Machine-processable by any software

- Version-controlled in Git

- Validated using JSON Schema

 

### Structure

 

```json

{

  "inputs": {

    "designRequirements": {

      "magnetizingInductance": {"minimum": 0.001},

      "turnsRatios": [{"nominal": 10}]

    },

    "operatingPoints": [{

      "name": "nominal",

      "excitationsPerWinding": [{

        "frequency": 100000,

        "current": {

          "waveform": {"data": [...], "time": [...]},

          "processed": {"rms": 5.0, "peak": 8.0}

        },

        "voltage": {

          "waveform": {"data": [...], "time": [...]},

          "processed": {"rms": 48.0, "peak": 68.0}

        }

      }]

    }]

  },

  "magnetic": {

    "core": {

      "functionalDescription": {

        "shape": "ETD 39",

        "material": "3C95",

        "gapping": [{"type": "centered", "length": 0.0005}]

      }

    },

    "coil": {

      "bobbin": "ETD 39",

      "functionalDescription": [{

        "name": "primary",

        "numberTurns": 20,

        "wire": "AWG 22"

      }, {

        "name": "secondary",

        "numberTurns": 200,

        "wire": "AWG 30"

      }]

    }

  },

  "outputs": {

    "coreLosses": 0.5,

    "windingLosses": [0.3, 0.2],

    "leakageInductance": 0.00001,

    "temperatureRise": 35

  }

}

```

 

### Key Benefits for Our Framework

 

1. **Import/Export**: Save designs in MAS format for interoperability

2. **Database Queries**: Use MAS schemas to query OpenMagnetics catalogs

3. **Validation**: JSON Schema validates design completeness

4. **FEA Export**: MAS → MVB → ANSYS Maxwell workflow

 

---

 

## Integration Strategy

 

### Phase 1: Database Integration (Low Risk, High Value)

 

**Goal**: Use OpenMagnetics as a core/material database source

 

```python

# backend/integrations/openmagnetics.py

 

import PyMKF

from typing import List, Optional

from models.transformer import CoreSpec

 

class OpenMagneticsDB:

    """Interface to OpenMagnetics core database"""

 

    def __init__(self):

        self._cores = None

        self._materials = None

 

    @property

    def cores(self) -> List[dict]:

        if self._cores is None:

            self._cores = PyMKF.get_available_cores()

        return self._cores

 

    def find_cores_by_ap(

        self,

        target_ap_cm4: float,

        tolerance: float = 0.1,

        material_type: Optional[str] = None,

        geometry: Optional[str] = None

    ) -> List[CoreSpec]:

        """

        Find cores matching Area Product requirement

 

        Args:

            target_ap_cm4: Target Ap in cm⁴

            tolerance: Acceptable deviation (0.1 = ±10%)

            material_type: Filter by material (e.g., "ferrite", "silicon_steel")

            geometry: Filter by shape (e.g., "ETD", "EI", "toroid")

 

        Returns:

            List of matching CoreSpec objects

        """

        matches = []

 

        for core in self.cores:

            try:

                Ae = core["processedDescription"]["columns"][0]["area"]

                Wa = core["processedDescription"]["windingWindows"][0]["area"]

                Ap_cm4 = Ae * Wa * 1e8  # m² × m² → cm⁴

 

                if abs(Ap_cm4 - target_ap_cm4) / target_ap_cm4 <= tolerance:

                    # Apply filters

                    if geometry and geometry.lower() not in core["functionalDescription"]["shape"].lower():

                        continue

 

                    matches.append(self._convert_to_core_spec(core, Ap_cm4))

 

            except (KeyError, TypeError):

                continue

 

        return sorted(matches, key=lambda x: abs(x.Ap_cm4 - target_ap_cm4))

 

    def _convert_to_core_spec(self, om_core: dict, ap_cm4: float) -> CoreSpec:

        """Convert OpenMagnetics core format to our CoreSpec model"""

        return CoreSpec(

            manufacturer=om_core["manufacturerInfo"].get("manufacturer", "Unknown"),

            part_number=om_core["manufacturerInfo"]["reference"],

            geometry=om_core["functionalDescription"]["shape"],

            material=om_core["functionalDescription"]["material"],

            Ae_cm2=om_core["processedDescription"]["columns"][0]["area"] * 1e4,

            Wa_cm2=om_core["processedDescription"]["windingWindows"][0]["area"] * 1e4,

            Ap_cm4=ap_cm4,

            # Additional fields from processedDescription...

        )

 

    def get_material_properties(self, material_name: str) -> dict:

        """Get material properties (Steinmetz coefficients, Bsat, etc.)"""

        # Query OpenMagnetics material database

        pass

```

 

### Phase 2: Calculation Validation

 

**Goal**: Cross-validate our McLyman calculations against OpenMagnetics models

 

```python

# backend/calculations/validation.py

 

from integrations.openmagnetics import OpenMagneticsDB

import PyMKF

 

def validate_core_loss(

    our_calculation: float,

    core: dict,

    frequency: float,

    Bac: float,

    temperature: float = 100

) -> dict:

    """

    Compare our core loss calculation to OpenMagnetics

 

    Returns:

        {

            "our_value": float,

            "om_value": float,

            "difference_percent": float,

            "status": "pass" | "warning" | "fail"

        }

    """

    # Build OpenMagnetics excitation

    excitation = {

        "frequency": frequency,

        "processed": {

            "peakToPeak": 2 * Bac

        }

    }

 

    # Calculate using OpenMagnetics

    om_loss = PyMKF.calculate_core_losses(core, excitation, temperature)

 

    diff = abs(our_calculation - om_loss["volumetricLosses"]) / om_loss["volumetricLosses"]

 

    return {

        "our_value": our_calculation,

        "om_value": om_loss["volumetricLosses"],

        "difference_percent": diff * 100,

        "status": "pass" if diff < 0.1 else ("warning" if diff < 0.2 else "fail")

    }

```

 

### Phase 3: MAS Export

 

**Goal**: Export designs in MAS format for FEA and CAD workflows

 

```python

# backend/export/mas_exporter.py

 

import json

from typing import Optional

from models.transformer import TransformerDesign

 

def export_to_mas(design: TransformerDesign, filepath: Optional[str] = None) -> dict:

    """

    Export transformer design to MAS (Magnetic Agnostic Structure) format

 

    This enables:

    - Import into OpenMagnetics web UI

    - FEA model generation via MVB → FreeCAD/ANSYS

    - Sharing with other engineers using MAS-compatible tools

    """

    mas_doc = {

        "inputs": {

            "designRequirements": {

                "name": design.name,

                "magnetizingInductance": {"nominal": design.Lm} if design.Lm else None,

                "turnsRatios": [{"nominal": design.turns_ratio}]

            },

            "operatingPoints": [{

                "name": "nominal",

                "excitationsPerWinding": [

                    _build_excitation(design.primary),

                    _build_excitation(design.secondary)

                ]

            }]

        },

        "magnetic": {

            "core": {

                "functionalDescription": {

                    "shape": design.core.part_number,

                    "material": design.core.material,

                    "gapping": _build_gapping(design.air_gap)

                }

            },

            "coil": {

                "functionalDescription": [

                    {

                        "name": "primary",

                        "numberTurns": design.Np,

                        "wire": design.primary_wire

                    },

                    {

                        "name": "secondary",

                        "numberTurns": design.Ns,

                        "wire": design.secondary_wire

                    }

                ]

            }

        },

        "outputs": {

            "coreLosses": design.core_loss_W,

            "windingLosses": [design.primary_copper_loss_W, design.secondary_copper_loss_W],

            "temperatureRise": design.temp_rise_C

        }

    }

 

    if filepath:

        with open(filepath, 'w') as f:

            json.dump(mas_doc, f, indent=2)

 

    return mas_doc

 

def _build_excitation(winding) -> dict:

    """Build excitation dict for a winding"""

    return {

        "frequency": winding.frequency,

        "current": {

            "processed": {

                "rms": winding.Irms,

                "peak": winding.Ipk,

                "dutyCycle": winding.duty_cycle

            }

        },

        "voltage": {

            "processed": {

                "rms": winding.Vrms,

                "peak": winding.Vpk

            }

        }

    }

 

def _build_gapping(air_gap) -> list:

    """Build gapping description"""

    if not air_gap or air_gap == 0:

        return []

    return [{"type": "centered", "length": air_gap}]

```

 

### Phase 4: Pulse Transformer Validation

 

**Challenge**: OpenMagnetics is primarily designed for SMPS (high-frequency switching) applications. Pulse transformer support needs validation.

 

**Approach**:

1. Test if iGSE/NSE models handle millisecond pulses correctly

2. Validate against known pulse transformer designs

3. Implement fallback to McLyman method if OpenMagnetics models are inadequate

 

```python

# backend/calculations/pulse_validation.py

 

def validate_pulse_transformer_model(

    pulse_waveform: dict,

    core: dict,

    temperature: float

) -> dict:

    """

    Test if OpenMagnetics models are valid for pulse transformer operation

 

    Pulse characteristics that may challenge OpenMagnetics:

    - Very low duty cycle (< 5%)

    - Millisecond pulse widths (not microsecond)

    - Non-sinusoidal, capacitor-discharge waveforms

    - Extreme peak currents (1000s of amps)

    """

    # Build excitation with pulse waveform

    excitation = {

        "frequency": pulse_waveform["repetition_rate"],

        "waveform": {

            "data": pulse_waveform["voltage_data"],

            "time": pulse_waveform["time_data"]

        }

    }

 

    try:

        result = PyMKF.calculate_core_losses(core, excitation, temperature)

        return {

            "supported": True,

            "model_used": result.get("model", "unknown"),

            "losses": result["volumetricLosses"],

            "notes": []

        }

    except Exception as e:

        return {

            "supported": False,

            "model_used": None,

            "losses": None,

            "notes": [f"OpenMagnetics error: {str(e)}", "Falling back to McLyman method"]

        }

```

 

---

 

## API Endpoint Integration

 

### New Endpoints for OpenMagnetics Features

 

**File:** `backend/routers/openmagnetics.py`

 

```python

from fastapi import APIRouter, Query

from integrations.openmagnetics import OpenMagneticsDB

from export.mas_exporter import export_to_mas

 

router = APIRouter(prefix="/api/openmagnetics", tags=["OpenMagnetics Integration"])

 

om_db = OpenMagneticsDB()

 

@router.get("/cores/search")

async def search_cores(

    ap_cm4: float = Query(..., description="Target Area Product [cm⁴]"),

    tolerance: float = Query(0.1, description="Tolerance (0.1 = ±10%)"),

    geometry: str = Query(None, description="Core geometry filter"),

    material: str = Query(None, description="Material filter")

):

    """Search OpenMagnetics database for suitable cores"""

    return om_db.find_cores_by_ap(ap_cm4, tolerance, material, geometry)

 

@router.get("/cores/{part_number}")

async def get_core_details(part_number: str):

    """Get detailed core specifications from OpenMagnetics"""

    for core in om_db.cores:

        if core["manufacturerInfo"]["reference"] == part_number:

            return core

    return {"error": f"Core {part_number} not found"}

 

@router.post("/export/mas")

async def export_design_mas(design_id: str):

    """Export a saved design to MAS format"""

    # Load design from database

    # design = load_design(design_id)

    # return export_to_mas(design)

    pass

 

@router.post("/validate/core-loss")

async def validate_core_loss_calculation(

    core_part_number: str,

    frequency: float,

    Bac: float,

    our_calculation: float,

    temperature: float = 100

):

    """Cross-validate core loss calculation against OpenMagnetics"""

    # Implementation as shown above

    pass

```

 

---

 

## Frontend Integration

 

### Core Selection with OpenMagnetics Data

 

**File:** `frontend/components/CoreSelectorOM.vue`

 

```vue

<template>

  <div class="core-selector">

    <h3>Core Selection (OpenMagnetics Database)</h3>

 

    <!-- Search Parameters -->

    <div class="search-params">

      <label>Target Ap: {{ targetAp.toFixed(2) }} cm⁴</label>

      <input type="range" v-model="targetAp" min="0.1" max="1000" step="0.1">

 

      <label>Tolerance: ±{{ (tolerance * 100).toFixed(0) }}%</label>

      <input type="range" v-model="tolerance" min="0.05" max="0.3" step="0.01">

 

      <select v-model="geometry">

        <option value="">All Geometries</option>

        <option value="ETD">ETD</option>

        <option value="EE">EE</option>

        <option value="PQ">PQ</option>

        <option value="RM">RM</option>

        <option value="EI">EI Laminated</option>

        <option value="toroid">Toroid</option>

      </select>

    </div>

 

    <!-- Results -->

    <div class="core-results">

      <table>

        <thead>

          <tr>

            <th>Part Number</th>

            <th>Manufacturer</th>

            <th>Ae (cm²)</th>

            <th>Wa (cm²)</th>

            <th>Ap (cm⁴)</th>

            <th>Select</th>

          </tr>

        </thead>

        <tbody>

          <tr v-for="core in matchingCores" :key="core.part_number">

            <td>{{ core.part_number }}</td>

            <td>{{ core.manufacturer }}</td>

            <td>{{ core.Ae_cm2.toFixed(2) }}</td>

            <td>{{ core.Wa_cm2.toFixed(2) }}</td>

            <td>{{ core.Ap_cm4.toFixed(2) }}</td>

            <td><button @click="selectCore(core)">Select</button></td>

          </tr>

        </tbody>

      </table>

    </div>

  </div>

</template>

 

<script setup>

import { ref, watch } from 'vue'

import { useDesignStore } from '@/stores/design'

 

const store = useDesignStore()

 

const targetAp = ref(10)

const tolerance = ref(0.1)

const geometry = ref('')

const matchingCores = ref([])

 

async function searchCores() {

  const params = new URLSearchParams({

    ap_cm4: targetAp.value,

    tolerance: tolerance.value,

    ...(geometry.value && { geometry: geometry.value })

  })

 

  const response = await fetch(`/api/openmagnetics/cores/search?${params}`)

  matchingCores.value = await response.json()

}

 

function selectCore(core) {

  store.setCore(core)

}

 

// Debounced search on parameter change

watch([targetAp, tolerance, geometry], searchCores, { immediate: true })

</script>

```

 

### MAS Export Button

 

```vue

<template>

  <button @click="exportMAS" class="export-btn">

    📦 Export to MAS

  </button>

</template>

 

<script setup>

async function exportMAS() {

  const response = await fetch('/api/openmagnetics/export/mas', {

    method: 'POST',

    headers: { 'Content-Type': 'application/json' },

    body: JSON.stringify({ design_id: currentDesignId })

  })

 

  const masDoc = await response.json()

 

  // Download as JSON file

  const blob = new Blob([JSON.stringify(masDoc, null, 2)], { type: 'application/json' })

  const url = URL.createObjectURL(blob)

  const a = document.createElement('a')

  a.href = url

  a.download = `transformer_design_${currentDesignId}.mas.json`

  a.click()

}

</script>

```

 

---

 

## Installation Requirements

 

### Python Dependencies

 

```toml

# pyproject.toml additions

 

[project.dependencies]

PyMKF = ">=0.1.0"  # OpenMagnetics Python bindings

```

 

### Build Requirements

 

PyMKF requires C++ compilation. Installation options:

 

**Option 1: pip install (if wheels available)**

```bash

pip install PyMKF

```

 

**Option 2: Build from source**

```bash

git clone https://github.com/OpenMagnetics/PyMKF.git

cd PyMKF

pip install -r requirements.txt

python setup.py build

python setup.py install

```

 

**Option 3: Use WebLibMKF via REST API**

If PyMKF compilation is problematic, call OpenMagnetics web backend directly:

```python

import requests

 

def query_openmagnetics_api(endpoint: str, data: dict) -> dict:

    response = requests.post(

        f"https://openmagnetics.com/api/{endpoint}",

        json=data

    )

    return response.json()

```

 

---

 

## Risk Assessment

 

### Technical Risks

 

| Risk | Likelihood | Impact | Mitigation |

|------|------------|--------|------------|

| PyMKF compilation issues on Windows | Medium | High | Use REST API fallback or WebLibMKF |

| OpenMagnetics API changes | Low | Medium | Version-lock PyMKF, implement adapter pattern |

| Pulse transformer models inaccurate | Medium | Medium | Validate against known designs, McLyman fallback |

| Database incomplete for laminated cores | Medium | Low | Supplement with our own JSON database |

 

### Dependency Risks

 

| Dependency | Risk | Mitigation |

|------------|------|------------|

| PyMKF maintenance | Low (MIT, active) | Fork if abandoned |

| OpenMagnetics web service | Medium | Local database fallback |

| MAS schema changes | Low | Version-lock schema |

 

---

 

## Implementation Timeline

 

| Phase | Tasks | Effort | Dependencies |

|-------|-------|--------|--------------|

| **1a** | Install PyMKF, test basic queries | 2-3 hours | None |

| **1b** | Build `OpenMagneticsDB` wrapper class | 3-4 hours | 1a |

| **1c** | Integrate core search into existing API | 2-3 hours | 1b |

| **2a** | Implement calculation validation | 3-4 hours | 1b |

| **2b** | Test pulse transformer compatibility | 2-3 hours | 2a |

| **3a** | Implement MAS export | 3-4 hours | 1b |

| **3b** | Frontend OpenMagnetics components | 3-4 hours | 1c |

| **Total** | | **18-25 hours** | |

 

---

 

## Success Criteria

 

1. ✅ Can query OpenMagnetics for cores matching Ap requirement

2. ✅ Core selection UI shows OpenMagnetics database results

3. ✅ Our core loss calculations match OpenMagnetics within 10%

4. ✅ Can export designs to MAS format

5. ✅ MAS exports import correctly into OpenMagnetics web UI

6. ⚠️ Pulse transformer models validated (or documented limitations)

 

---

 

## Open Questions for User

 

1. **PyMKF Installation**: Have you used PyMKF before? Any known compilation issues on your system?

 

2. **Database Priority**: Should OpenMagnetics be:

   - Option A: Primary database (replace our JSON)

   - Option B: Supplementary database (query when our JSON lacks match)

   - Option C: Validation only (use our database, cross-check with OpenMagnetics)

 

3. **Web API Fallback**: If PyMKF compilation fails, acceptable to use OpenMagnetics REST API (requires internet)?

 

4. **FEA Integration**: Interested in MVB → FreeCAD/ANSYS workflow for pulse transformer FEA?

 

---

 

## References

 

- [OpenMagnetics Website](https://openmagnetics.com/)

- [OpenMagnetics GitHub](https://github.com/OpenMagnetics)

- [MAS (Magnetic Agnostic Structure)](https://github.com/OpenMagnetics/MAS)

- [PyMKF Python Bindings](https://github.com/OpenMagnetics/PyMKF)

- [MKF C++ Engine](https://github.com/OpenMagnetics/MKF)

- [IEEE PELS Article: OpenMagnetics Toolbox](https://www.ieee-pels.org/magazine/openmagnetics-an-online-toolbox-for-designing-and-simulating-magnetics/)

- [Ansys + OpenMagnetics Webinar](https://www.ansys.com/webinars/democratizing-magnetic-component-design)

 