# Power Transformer Designer — User Guide

## Overview
Full-stack design tool for power, inductor, and pulse transformers. Backend: FastAPI in [backend/main.py](backend/main.py); frontend: Nuxt 3 in [frontend/pages/](frontend/pages/index.vue).

## Prerequisites
- Python (via uv) for backend; Node 18+ for frontend.
- Clone repository and run commands from project root.

## Setup & Run
1. **Backend**
   ```bash
   cd backend
   uv run uvicorn main:app --host 127.0.0.1 --port 8000
   ```
   - API docs: http://localhost:8000/docs
2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   - UI: http://localhost:3000/

## Using the Designer
### Transformer Design
- Open **Design → Transformer** (`/design/transformer`).
- Enter requirements (power, frequency, voltages, duty, waveform).
- Results show core, winding, losses, thermal. Alternative cores appear with OpenMagnetics badges.

### Inductor Design
- Open **Design → Inductor** (`/design/inductor`).
- Provide inductance, current, ripple, frequency. Backend endpoint in [backend/routers/inductor.py](backend/routers/inductor.py) returns sizing; UI currently basic.

### Pulse Transformer
- Open **Design → Pulse** (`/design/pulse`).
- Supply source cap/voltage, pulse width, repetition, isolation needs. Backend logic in [backend/calculations/pulse_transformer.py](backend/calculations/pulse_transformer.py) and [backend/routers/pulse_transformer.py](backend/routers/pulse_transformer.py).

## Exports
- API endpoints available in [backend/routers/export.py](backend/routers/export.py):
  - `POST /api/export/mas` — MAS JSON (OpenMagnetics)
  - `POST /api/export/femm` — FEMM Lua script
  - `POST /api/export/json/download` — Raw design JSON
- Frontend buttons to be wired (see plan); until then, call API directly or via Swagger UI.

## Data Sources
- Local cores: [backend/data/cores.json](backend/data/cores.json)
- Materials: [backend/data/materials.json](backend/data/materials.json)
- OpenMagnetics integration: [backend/integrations/openmagnetics.py](backend/integrations/openmagnetics.py)

## Tips
- For high-frequency designs (>50 kHz), prefer Litz (planned auto-selection).
- Validate losses with temperature; material curves are limited locally.
- Use Swagger to sanity-check requests/responses before UI changes.

## Support
For issues, start with backend logs (uvicorn) and frontend console. Key files: [backend/tests/](backend/tests/__init__.py) for coverage, [frontend/composables/useTransformerDesign.ts](frontend/composables/useTransformerDesign.ts) for client API calls.
