# Silicon-Steel EI Core Research Report

**Date**: 2025-12-08  
**Purpose**: Guide for engineers on laminated silicon-steel E/I cores for LF pulse transformers

---

## 1. Key Manufacturers

| Manufacturer | Location | Product Line | Data Format |
|--------------|----------|--------------|-------------|
| **Grau-Stanzwerk** | Germany | EI laminations (DIN EN 60740-1) | PDF catalog |
| **GNEE EC** | China | EI, UI, three-phase laminations | PDF specs |
| **Centersky** | China | CRGO/CRNGO EI cores (EI28-EI240) | PDF |
| **JFE Steel** | Japan | G-CORE, JNEX-Core sheet steel | PDF, inquire for digital |
| **Nippon Steel** | Japan | Grain-oriented electrical steel | PDF |
| **Kunal Stamping** | India | Custom EI laminations | PDF, custom |
| **Sewa Electrical** | India | EI laminations | PDF |

> **Note**: No manufacturers provide CSV/JSON databases publicly. Data must be extracted from PDF catalogs.

---

## 2. HF vs LF Transformer Comparison

| Parameter | **HF Transformer** (Ferrite) | **LF Transformer** (Silicon Steel) |
|-----------|------------------------------|-------------------------------------|
| **Frequency Range** | 20 kHz – 1 MHz | 50 Hz – 400 Hz |
| **Bmax (Saturation)** | 0.2 – 0.35 T | 1.2 – 1.7 T |
| **Typical Bmax (design)** | 0.15 – 0.25 T | 1.0 – 1.5 T |
| **Core Loss @Bmax** | 100-500 mW/cm³ (100kHz) | 0.9-1.5 W/kg (50Hz, 1.5T) |
| **Permeability (µr)** | 2,000 – 10,000 | 5,000 – 50,000 |
| **Core Type** | Toroid, EE, ETD, PQ | EI, UI, C-core laminations |
| **Power Range** | mW – 10 kW | W – 10+ MW |
| **Skin Depth** | Important (Litz wire needed) | Negligible at LF |
| **Why this matters** | High freq = small size but low Bmax | Low freq = large size but high Bmax |

### Key Insight
**For pulse transformers at 125 Hz with ms-range pulses**, silicon-steel is ideal because:
- **6× higher Bmax** → smaller core for same volt-seconds
- **No skin effect issues** at low frequency
- **Standard EI cores readily available**

---

## 3. EI Lamination Dimensions (DIN EN 60740-1)

Standard EI laminations follow DIN EN 60740-1 (formerly DIN 41302).

| EI Size | Tongue (c) | Window H×W | **Ae** [mm²] | **Wa** [mm²] | **Ap** [cm⁴] |
|---------|------------|------------|--------------|--------------|--------------|
| EI 30   | 10 mm      | 15 × 5 mm  | 100          | 75           | 0.075        |
| EI 48   | 16 mm      | 24 × 8 mm  | 256          | 192          | 0.49         |
| EI 60   | 20 mm      | 30 × 10 mm | 400          | 300          | 1.2          |
| EI 96   | 32 mm      | 48 × 16 mm | 1,024        | 768          | 7.9          |
| EI 120  | 40 mm      | 60 × 20 mm | 1,600        | 1,200        | 19.2         |
| EI 150  | 50 mm      | 75 × 25 mm | 2,500        | 1,875        | 46.9         |
| EI 192  | 64 mm      | 96 × 32 mm | 4,096        | 3,072        | 126          |

*Ae = c² (square stack), Wa = H × W, Ap = Ae × Wa × 10⁻⁴*

---

## 4. Material Properties

### Silicon Steel Grades (CRGO)

| Material | Thickness | Core Loss @1.5T/50Hz | Bsat | Applications |
|----------|-----------|----------------------|------|--------------|
| M3 (23Z110) | 0.23 mm | 0.80-0.92 W/kg | 1.85 T | High-efficiency transformers |
| M4 (27Z130) | 0.27 mm | 0.92-1.10 W/kg | 1.85 T | Distribution transformers |
| M5 (30G130) | 0.30 mm | 1.00-1.30 W/kg | 1.85 T | General purpose |
| M6 (35G155) | 0.35 mm | 1.20-1.55 W/kg | 1.85 T | Cost-effective |

**For pulse applications at 125 Hz**: M4 or M5 grade, 0.30-0.35mm thickness is suitable.

---

## 5. Core Loss at Different Frequencies

| Frequency | Core Loss @1.5T (CRGO) |
|-----------|------------------------|
| 50 Hz     | 0.9 – 1.5 W/kg        |
| 60 Hz     | 1.1 – 1.8 W/kg        |
| 125 Hz    | ~2.0 – 3.0 W/kg       |
| 400 Hz    | ~5 – 10 W/kg          |

*Note: At 125 Hz (Dropless application), expect ~2× the loss of 50 Hz operation.*

---

## 6. Data Availability Summary

| Source | Format | Ae/Wa Data | Core Loss | Downloadable |
|--------|--------|------------|-----------|--------------|
| Grau-Stanzwerk | PDF | Dimensions only | No | PDF catalog |
| JFE Steel | PDF | Sheet specs | Yes | PDF only |
| OpenMagnetics | JSON | Ferrite only | Yes | ✅ Open source |
| Mag-Inc | PDF | Powder/ferrite | Yes | PDF only |

> **⚠️ Gap Identified**: No open-source silicon-steel core database exists. Would need to create one from manufacturer PDFs.

---

## 7. Recommended Next Steps

1. **For Dropless transformer**: Calculate required Ae, then select from EI 150-192 range
2. **For database**: Extract EI lamination specs from Grau-Stanzwerk or GNEE catalogs
3. **Core loss model**: Use Steinmetz equation with silicon-steel coefficients
