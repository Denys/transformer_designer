# Phase 3: Core Selection and Database Creation

**Date**: 2025-12-08  
**Status**: Complete

---

## 1. Core Search Results

Based on Phase 2 requirements (Ae ≥ 2.08 cm², Wa ≥ 17.5 cm²):

| Core | Ae [cm²] | Wa [cm²] | Ap [cm⁴] | Suitable? | Notes |
|------|----------|----------|----------|-----------|-------|
| EI-96 | 10.24 | 7.68 | 78.6 | ❌ | Wa too small |
| EI-120 | 16.0 | 12.0 | 192 | ❌ | Wa too small |
| **EI-150** | 25.0 | 18.75 | 469 | ✅ | Marginal for HV |
| **EI-192** | 40.96 | 30.72 | 1258 | ✅✅ | **Recommended** |
| EI-240 | 64.0 | 48.0 | 3072 | ✅ | Overkill |

### Recommended Core: **EI-192**

| Parameter | Value |
|-----------|-------|
| Overall dimensions | 192 × 160 mm |
| Tongue width | 64 mm |
| Window | 96 × 32 mm |
| Ae | 40.96 cm² |
| Wa | 30.72 cm² |
| Weight | ~9 kg |
| Material | CRGO M5 (0.30mm) |

**Sources**: Benaka Electronics, Centersky catalogs

---

## 2. Database Created

### Files Created

| File | Description |
|------|-------------|
| `backend/data/silicon_steel_cores.json` | Core database (7 EI cores) |
| `backend/integrations/silicon_steel.py` | Python loader module |

### Database Schema

```json
{
  "cores": [
    {
      "part_number": "EI-192",
      "geometry": "EI",
      "Ae_cm2": 40.96,
      "Wa_cm2": 30.72,
      "Ap_cm4": 1258.3,
      "lm_cm": 28.8,
      "MLT_cm": 22.4,
      "Bmax_T": 1.5,
      "weight_g": 9024,
      "material_grade": "M5"
    }
  ],
  "material_grades": {
    "M5": {
      "thickness_mm": 0.30,
      "core_loss_W_kg_1_5T_50Hz": 1.15,
      "Bsat_T": 1.85
    }
  }
}
```

### Python API

```python
from integrations.silicon_steel import get_silicon_steel_db

db = get_silicon_steel_db()

# Find cores for Dropless
cores = db.find_suitable_cores(
    required_Ae_cm2=2.08,
    required_Wa_cm2=17.5,
    geometry="EI"
)
```

---

## 3. Integration with Pulse Router

To use silicon-steel cores for HV power pulse designs, add to `routers/pulse_transformer.py`:

```python
from integrations.silicon_steel import get_silicon_steel_db

# In design_pulse_transformer():
if is_hv_power_pulse:
    ss_db = get_silicon_steel_db()
    cores = ss_db.find_suitable_cores(
        required_Ae_cm2=required_Ae_cm2,
        required_Wa_cm2=required_Wa_cm2,
        geometry="EI"
    )
```

---

## 4. Summary

| Deliverable | Status |
|-------------|--------|
| Core research report | ✅ `steel_core_research.md` |
| Dropless specs | ✅ `dropless_specs.md` |
| Core database JSON | ✅ `silicon_steel_cores.json` |
| Python loader | ✅ `silicon_steel.py` |
| Recommended core | **EI-192** |
