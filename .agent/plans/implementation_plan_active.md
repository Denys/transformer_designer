# Power Transformer Designer — Consolidated Implementation Plan

**Status**: Planning + Readiness Assessment (2025-12-10)
**Scope**: Merge prior plans into a single active document; mark prior plans as archived references.

---

## 1) Current Readiness Snapshot

- **Backend**: ~90% (FastAPI endpoints in [backend/routers/](backend/routers/__init__.py) with core calculations in [backend/calculations/](backend/calculations/__init__.py)).
- **Frontend**: ~85% (Nuxt pages in [frontend/pages/](frontend/pages/index.vue) with composables in [frontend/composables/](frontend/composables/useTransformerDesign.ts)).
- **OpenMagnetics Integration**: ~90% ([backend/integrations/openmagnetics.py](backend/integrations/openmagnetics.py)).
- **Export APIs**: Present ([backend/routers/export.py](backend/routers/export.py)) but UI hooks incomplete.
- **Testing**: ~40% coverage ([backend/tests/](backend/tests/__init__.py)).
- **Docs**: Minimal; new root user guide pending.

---

## 2) Critical Gaps (blockers / correctness)
1) **MLT/At defaults for OM cores** — needs geometry-derived values in [backend/routers/transformer.py](backend/routers/transformer.py) and helpers in [backend/integrations/openmagnetics.py](backend/integrations/openmagnetics.py).
2) **Layer estimation rough (Np//20)** — refine based on bobbin geometry in [backend/routers/transformer.py](backend/routers/transformer.py) or [backend/calculations/winding.py](backend/calculations/winding.py).
3) **Bac assumption (Bmax/2) for non-sinusoidal waveforms** — adjust waveform handling in [backend/calculations/ap_method.py](backend/calculations/ap_method.py) and consumers.
4) **No automatic Litz selection for HF** — add recommend_litz_wire + AC factor in [backend/calculations/winding.py](backend/calculations/winding.py) and frequency gate in [backend/routers/transformer.py](backend/routers/transformer.py).

---

## 3) High/Medium Gaps (functionality/UI)
5) **Export buttons absent in UI** — integrate with [frontend/pages/design/transformer.vue](frontend/pages/design/transformer.vue) and [frontend/composables/useExport.ts](frontend/composables/useExport.ts).
6) **Inductor frontend incomplete** — enhance [frontend/pages/design/inductor.vue](frontend/pages/design/inductor.vue) with full form + results.
7) **Pulse frontend needs polish** — review [frontend/pages/design/pulse.vue](frontend/pages/design/pulse.vue) for completeness and alignment with backend models.
8) **Design persistence missing** — add localStorage (and optional backend) in frontend composables.
9) **Core/material datasets limited** — expand [backend/data/cores.json](backend/data/cores.json) and [backend/data/materials.json](backend/data/materials.json).
10) **Export convenience** — add download helpers for MAS/FEMM/JSON in [frontend/composables/useExport.ts](frontend/composables/useExport.ts).

---

## 4) Lower Priority Enhancements
- Unit toggle (SI/Imperial) across UI/outputs.
- Design comparison view + charts.
- Winding diagram visualization.
- PDF report generation (ties to exports).
- STEP/3D export (future).

---

## 5) Implementation Plan (Active)

### Phase A — Correctness & HF readiness (6–8h)
**Objectives**
- Geometry-derived **MLT/At** fallbacks and layer estimation tied to real dimensions; no geometry-free heuristics.
- Waveform-aware **Bac** (no Bmax/2 default) across transformer design flow.
- **Litz** recommendation + AC factor with f > 50 kHz gate; surfaced in outputs.

**Success criteria (A1)**
- All Phase A tasks implemented and covered by unit tests in [backend/tests/](backend/tests/__init__.py).
- Transformer endpoint returns geometry-driven MLT/At, layer counts, waveform-correct Bac, and Litz metadata when applicable.
- HF and LF smoke tests pass without regressions.

**Progress snapshot**
| Task | Owner | Est | Status | % Complete | Coverage target |
|------|-------|-----|--------|------------|-----------------|
| Geometry-derived MLT/At | Backend Eng | 1.5h | Pending | 0% | Unit: ≥1 case per shape family |
| Layer estimation by window geometry | Backend Eng | 1.5h | Pending | 0% | Unit: ≥2 cases (narrow vs wide window) |
| Waveform-aware Bac | Backend Eng | 1h | Pending | 0% | Unit: ≥3 waveforms (sin/square/trapezoid) |
| Litz recommendation + AC factor | Backend Eng | 1.5h | Pending | 0% | Unit: ≥2 freq thresholds (≤50k, >50k) |
| API/flow validation + smoke | Backend Eng | 0.5h | Pending | 0% | Integration: transformer HF+LF |
**Overall Phase A completion:** 0% (weighted by estimates)

**Milestones**
- M1: Geometry MLT/At helpers in [backend/integrations/openmagnetics.py:1](backend/integrations/openmagnetics.py:1) consumed by [backend/routers/transformer.py:421](backend/routers/transformer.py:421).
- M2: Layer estimation replaces Np//20 heuristic in [backend/calculations/winding.py:1](backend/calculations/winding.py:1) and is returned via transformer response.
- M3: Waveform-aware Bac live in [backend/calculations/ap_method.py:1](backend/calculations/ap_method.py:1) and used in transformer flow.
- M4: Litz selection + AC factor applied and surfaced (gate f > 50 kHz) in [backend/calculations/winding.py:1](backend/calculations/winding.py:1) and [backend/routers/transformer.py:1](backend/routers/transformer.py:1).
- M5: Targeted unit + integration tests added; HF/LF smoke scenarios green.

**Task breakdown (with acceptance & tests)**
1) Geometry-derived MLT/At (Owner: Backend Eng, Est: 1.5h)
   - Implement shape-aware formulas (E/ETD/ER/EQ/EFD/EP/PQ/PM, toroids) using processedDescription {width,height,depth} (m→cm) with safety factors in [backend/integrations/openmagnetics.py:1](backend/integrations/openmagnetics.py:1).
   - Wire fallbacks in [backend/routers/transformer.py:421](backend/routers/transformer.py:421); guard null/zero.
   - Acceptance: No default constants used when geometry present; returned MLT/At non-zero and plausible.
   - Tests: Unit stubs with representative OM cores; assert MLT/At > 0 and within tolerance in [backend/tests/test_api.py:1](backend/tests/test_api.py:1) or dedicated unit tests.

2) Layer estimation from window geometry (Owner: Backend Eng, Est: 1.5h)
   - Compute turns-per-layer from window/bobbin dims and copper fill factor; remove Np//20 heuristic in [backend/calculations/winding.py:1](backend/calculations/winding.py:1).
   - Surface layer_count/window_utilization in transformer result via [backend/routers/transformer.py:1](backend/routers/transformer.py:1) and models if needed.
   - Acceptance: Layer count decreases with narrower window and increases with more turns; no hard-coded divisor remains.
   - Tests: Two geometries (narrow vs wide) show monotonic change; check response fields in [backend/tests/test_winding.py:1](backend/tests/test_winding.py:1) or [backend/tests/test_api.py:1](backend/tests/test_api.py:1).

3) Waveform-aware Bac (Owner: Backend Eng, Est: 1h)
   - Implement Bac per waveform (sin, square, triangular, trapezoidal, custom duty) in [backend/calculations/ap_method.py:1](backend/calculations/ap_method.py:1).
   - Ensure transformer design uses computed Bac (no Bmax/2 default) in [backend/routers/transformer.py:1](backend/routers/transformer.py:1).
   - Acceptance: Bac matches expected coefficients per waveform; defaults never Bmax/2 except where justified.
   - Tests: Unit cases per waveform in [backend/tests/test_ap_method.py:1](backend/tests/test_ap_method.py:1); integration ensures transformer output Bac aligns with input waveform.

4) Litz recommendation + AC factor (Owner: Backend Eng, Est: 1.5h)
   - Add recommend_litz_wire (skin-depth-based strand AWG, bundle sizing) and AC factor helpers in [backend/calculations/winding.py:1](backend/calculations/winding.py:1).
   - Apply f > 50 kHz gate (or explicit flag) and propagate litz metadata into transformer response via [backend/routers/transformer.py:1](backend/routers/transformer.py:1).
   - Acceptance: For f > 50 kHz, litz selected with strand count/awg/outer_diameter/ac_factor; for LF, standard wire path unchanged.
   - Tests: Two frequencies (e.g., 20 kHz no-litz, 100 kHz litz) in [backend/tests/test_winding.py:1](backend/tests/test_winding.py:1) and integration in [backend/tests/test_api.py:1](backend/tests/test_api.py:1).

5) Tests & smoke validation (Owner: Backend Eng, Est: 0.5h)
   - Add/extend unit tests covering the above in [backend/tests/test_winding.py:1](backend/tests/test_winding.py:1), [backend/tests/test_ap_method.py:1](backend/tests/test_ap_method.py:1); optional flow checks in [backend/tests/test_api.py:1](backend/tests/test_api.py:1).
   - Run HF (e.g., 100 kHz) and LF (e.g., 50 Hz) transformer requests; verify responses contain geometry-derived MLT/At, layer_count, waveform Bac, and litz metadata when applicable.
   - Acceptance: All new tests pass; smoke scenarios match expectations and do not regress existing outputs.

**Test coverage requirement**
- Phase A additions must be covered by unit tests (geometry, layers, Bac, Litz). Aim to raise coverage of touched modules (winding/ap_method/transformer flow) to ≥70% lines/branches where feasible for new/changed logic.

### Phase B — UX parity & exports (6–8h)
- Wire **Export buttons** (MAS/FEMM/JSON) into transformer page; finish [frontend/composables/useExport.ts](frontend/composables/useExport.ts).
- Complete **Inductor** and **Pulse** pages to parity with backend outputs.
- Add **design persistence** (localStorage) for recent designs.

### Phase C — Data depth & visualization (8–12h)
- Expand **cores/materials** datasets with key ferrites and silicon steel; add temp curves.
- Add **charts/visuals** (loss vs frequency/temp) and optional winding diagram stub.

### Phase D — Production readiness (as scheduled)
- Increase tests toward 80% (unit + API + basic E2E).
- Containerization and CI/CD wiring.
- PDF report template and doc set.

---

## 6) Readiness Checkpoints
- **A1**: MLT/At + Bac + Litz implemented and covered by unit tests in [backend/tests/](backend/tests/__init__.py).
- **B1**: Export UI live; inductor/pulse pages feature-complete; persistence shipped.
- **C1**: Datasets expanded; visuals added; export convenience verified.
- **D1**: Test coverage trend upward; container build green; docs present.

---

## 7) Archival Notes
- Superseded plans remain in place for reference: [comprehensive_implementation_plan_2025-12-07.md](comprehensive_implementation_plan_2025-12-07.md) and [implementation_plan_merged.md](implementation_plan_merged.md). Treat this document as the single active implementation plan going forward.
