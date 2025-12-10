# Project Folder Architecture Report

## Current Layout (summarized)
- [backend/](backend/README.md) — FastAPI app, calcs, integrations, routers, tests.
- [frontend/](frontend/nuxt.config.ts) — Nuxt 3 app (pages, composables, assets, .nuxt build artifacts present).
- [.agent/](.agent/plans/implementation_plan_active.md) — Plans and status docs.
- [pdfs/](pdfs/github_repos.txt) — Reference materials.
- Misc root docs: [ANTIGRAVITY_SP_v2.3_NOVA.md](ANTIGRAVITY_SP_v2.3_NOVA.md), [power_transformer_framework_plan.md](power_transformer_framework_plan.md), [user_guide.md](user_guide.md).

## Observations
- Backend is cleanly segmented: calculations in [backend/calculations/](backend/calculations/__init__.py), routers in [backend/routers/](backend/routers/__init__.py), integrations in [backend/integrations/](backend/integrations/__init__.py), tests in [backend/tests/](backend/tests/__init__.py).
- Frontend contains committed [.nuxt/](frontend/.nuxt/README.md) build artifacts; should be excluded from version control for cleanliness.
- Virtual env and cache folders exist in backend (`.venv/`, `.pytest_cache/`); keep git-ignored.
- PDF references live under [pdfs/](pdfs/github_repos.txt); fine to keep but consider moving to docs/ if published.

## Optimization Suggestions
1) **Prune build artifacts**: Remove and gitignore [frontend/.nuxt/](frontend/.nuxt/README.md); ensure `node_modules/` stays ignored.
2) **Consolidate docs**: Keep plans in [.agent/plans/](.agent/plans/implementation_plan_active.md) and user-facing docs at root; optionally move PDF references to `docs/` for clarity.
3) **Data separation**: Consider `data/` subfolders per domain (e.g., `data/core_catalogs/`, `data/materials/`) if datasets grow.
4) **Tests naming**: Maintain current `backend/tests/` layout; add mirrors for any new modules (export, persistence).
5) **Environment artifacts**: Keep `.venv/` local only; document uv usage in [backend/README.md](backend/README.md).

## Readiness Signal
Structure supports planned work; main housekeeping action is removing committed build output from [frontend/.nuxt/](frontend/.nuxt/README.md) and tightening docs/data organization as growth continues.
