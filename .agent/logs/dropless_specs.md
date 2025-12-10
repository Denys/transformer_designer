# Dropless Transformer Specifications

**Date**: 2025-12-08  
**Application**: High-power plasma DLC process power supply

---

## 1. Given Specifications (from Dropless_trafo.docx)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Primary voltage | 200 V | From capacitor bank |
| Primary capacitor | 2.0 mF | Energy storage |
| Peak primary current | **1,750 A** | Critical parameter |
| Pulse width | 2.4 – 2.8 ms | ~2.5 ms typical |
| Repetition rate | 125 Hz | 8 ms period |
| Secondary voltage | 3.0 – 3.5 kV | To plasma load |
| Secondary capacitor | 0.11 – 0.16 µF | Load capacitance |
| Primary turns | 1-2 turns | Specified |
| Secondary turns | ≥50 turns | Specified |
| Insulation | ≥4 kV continuous, 6 kV surge | Reinforced |
| Core type | Laminated silicon-steel E/I | No gap |
| Cooling | Natural convection | No forced air |

---

## 2. Calculated/Derived Specifications

### 2.1 Volt-Second Product

```
V·t = V × t_pulse
V·t = 200 V × 2.5 ms = 500 V·ms = 500,000 V·µs
```

| Parameter | Formula | Value |
|-----------|---------|-------|
| **Volt-second** | V × t | **500 V·ms** |

### 2.2 Required Core Effective Area (Ae)

Using Faraday's law:
```
V·t = N × Ae × ΔB
Ae = V·t / (N × ΔB)
```

For silicon-steel with **Bmax = 1.2 T** (conservative design):

| Np (turns) | ΔB (T) | Ae required | Ae (cm²) |
|------------|--------|-------------|----------|
| 1 | 1.2 | 500 V·ms / (1 × 1.2 T) = 416.7 mm² | **4.17 cm²** |
| 2 | 1.2 | 500 V·ms / (2 × 1.2 T) = 208.3 mm² | **2.08 cm²** |
| 2 | 1.5 | 500 V·ms / (2 × 1.5 T) = 166.7 mm² | **1.67 cm²** |

**Design choice: Np = 2, Bmax = 1.2 T → Ae ≥ 2.08 cm² = 208 mm²**

### 2.3 Turns Ratio

```
n = Ns / Np = Vs / Vp
n = 3500 V / 200 V = 17.5 (ideal)

Given: Np = 2, Ns = 50
Actual n = 50 / 2 = 25:1
```

| Parameter | Value |
|-----------|-------|
| Ideal turns ratio | 17.5:1 |
| Actual turns ratio | **25:1** (Np=2, Ns=50) |
| Secondary voltage (with 25:1) | 200 V × 25 = 5000 V (open circuit) |

### 2.4 Window Area (Wa)

Primary: 2 turns × 1750 A × 2.5 ms pulse → use foil/cable, ~175 mm² copper
Secondary: 50 turns × 70 A (= 1750/25) → wire, ~7 mm² copper per strand

Estimated wire cross-sections:
- Primary: **175 mm²** (foil or parallel cables)
- Secondary: **350 mm²** total (50 turns × ~7 mm² effective)

```
Fill factor Ku ≈ 0.3 (for HV insulation)
Wa_required = (175 + 350) / 0.3 = 1,750 mm² ≈ **17.5 cm²**
```

### 2.5 Core Selection

| EI Size | Ae [mm²] | Wa [mm²] | Ap [cm⁴] | Suitable? |
|---------|----------|----------|----------|-----------|
| EI 96   | 1,024    | 768      | 7.9      | ❌ Ae too small |
| EI 120  | 1,600    | 1,200    | 19.2     | ❌ Wa too small |
| EI 150  | 2,500    | 1,875    | 46.9     | ✅ Marginal |
| EI 192  | 4,096    | 3,072    | 126      | ✅ **Recommended** |

**Recommended core: EI 192 or larger custom lamination**

### 2.6 Core Volume and Weight

For EI 192 with square stack (64 mm):
```
Core volume ≈ Ae × magnetic path length
             ≈ 4,096 mm² × ~300 mm ≈ 1,230 cm³

Core weight = Volume × Density
            = 1,230 cm³ × 7.65 g/cm³ ≈ 9.4 kg
```

| Parameter | Value |
|-----------|-------|
| **Core volume** | ~1,200 – 1,500 cm³ |
| **Core weight** | **9 – 12 kg** |

### 2.7 Energy Transfer

```
Energy stored in primary capacitor:
E = 0.5 × C × V²
E = 0.5 × 2 mF × (200 V)² = 40 J per pulse

Power at 125 Hz:
P = E × f = 40 J × 125 Hz = 5,000 W average
```

| Parameter | Value |
|-----------|-------|
| Energy per pulse | **40 J** |
| Average power | **5 kW** |
| Peak power | ~350 kW (200V × 1750A) |

### 2.8 Core Loss Estimate

At 125 Hz, silicon steel M5 grade:
```
Core loss density ≈ 2.5 W/kg at 1.5T, 125Hz
Core loss = 2.5 W/kg × 10 kg ≈ 25 W
```

With 31% duty cycle (2.5ms/8ms):
```
Effective core loss ≈ 25 W × 0.31 ≈ 8 W (time-averaged)
```

---

## 3. Specifications Summary

| Parameter | Value | Unit |
|-----------|-------|------|
| Volt-second | 500 | V·ms |
| Turns ratio (Np:Ns) | 2:50 (1:25) | - |
| Required Ae (min) | 2.08 | cm² |
| Required Wa (min) | 17.5 | cm² |
| Recommended core | EI 192 | - |
| Core Ae | 4.1 | cm² |
| Core Wa | 30.7 | cm² |
| Core volume | ~1,300 | cm³ |
| Core weight | 10 ± 2 | kg |
| Energy per pulse | 40 | J |
| Average power | 5 | kW |
| Peak primary current | 1,750 | A |
| Primary wire | foil/cable | 175 mm² |
| Secondary wire | #10-12 AWG | 50 turns |
| Insulation clearance | ≥10 | mm |

---

## 4. Design Recommendations

1. **Core**: EI 192 or custom lamination with Ae ≥ 2.5 cm², Wa ≥ 20 cm²
2. **Primary winding**: 2 turns of copper foil (0.5-1mm thick × 100mm wide) or parallel cables
3. **Secondary winding**: 50 turns of #10 AWG, layer-wound with insulation between layers
4. **Insulation**: Triple-layer tape between pri/sec, ≥10mm creepage
5. **Core material**: CRGO M4/M5 grade, 0.30-0.35mm lamination thickness

---

**⏸️ PHASE 2 COMPLETE - Awaiting review before Phase 3**
