# Epic Standards: EPIC-002 Time-based Expiry

These are the **Inviolable Rules** for EPIC-002, extracted from the repository's local
configuration files (Primary Authority) and the established EPIC-001 behaviour. They are
referenced by `design.md` and `implementation.md` and must not be violated.

> Note: `product_standards/docs` does not exist in this repository, so all standards below are
> sourced from in-repo config and code. Where EPIC-001's `standards.md` and the live `ruff.toml`
> disagree, the live `ruff.toml` wins (local config is Primary Authority).

## Python & Backend (from `ruff.toml`, `Makefile`, `Dockerfile`)
- **Python Version**: 3.12 (`target-version = "py312"`; `python:3.12-slim` in `Dockerfile`).
- **Package Management**: `uv` only (`Makefile` uses `uv run`; `Dockerfile` builds with `uv`). Do not add `pip install` steps.
- **Lint/Format**: `ruff` with `line-length = 100`, `target-version = "py312"`.
  - Selected rule sets: `E, W, F, I, B, UP, N` (per live `ruff.toml` — note this is broader than EPIC-001's doc which omitted `W`).
  - `ignore = []` (live `ruff.toml`). Known inconsistency: existing code uses FastAPI `Depends(...)` in argument defaults, which is `B008`. Do **not** introduce *new* `B008` violations; if touching those signatures, keep the existing pattern.
  - Format: double quotes, space indent, magic trailing comma enabled, auto line endings.
  - `isort`: `known-first-party = ["backend"]`; section order `future, standard-library, third-party, first-party, local-trace`.

## Container & Infrastructure (from `Dockerfile`, `main.py`)
- **Base Image**: distroless-like `python:3.12-slim`, package managers purged, runs as non-root `appuser`.
- **Entrypoint**: `python -m src.backend.main`; persists via `/data` and `/config` volumes.
- **Service Design**: must run constantly (never terminate); hourly polling loop in `main.py` (`asyncio.sleep(3600)`).
- **Port**: HTTP port from `PORT` env var (default 8000).
- **Config Management**: single JSON config mounted at `/config/config.json`, **re-read every poll cycle** (`config_manager.load_config()` per cycle) — no rebuild needed. EPIC-002 must keep this live-reload behaviour (so `expiry_days` can change without a rebuild).
- **Logging**: structured JSON to stdout via `pythonjsonlogger.JsonFormatter` with `json_ensure_ascii=False` (see `main.py`).

## Data & State (from `db/state.py`)
- **Store**: SQLite `state.db` at `/data/state.db`. Episodes table currently has `pid` (PK), `status`, `filename`.
- **Lifecycle states**: `DOWNLOADED` and `SERVED` only. `SERVED` = expired/intentionally removed, never re-served, never re-downloaded.
- **Migration safety**: schema changes must be additive (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) and backfill-safe; existing state must survive an in-place upgrade.

## API & Output (from `api/feed.py`, `api/audio.py`, EPIC-001 US-004)
- **Framework**: FastAPI served by Uvicorn.
- **Feed**: single RSS feed at `/feed.xml`, AntennaPod-compatible, ordered by broadcast date oldest-first, one entry per `DOWNLOADED` episode, link + cover + metadata embedded.
- **Audio**: streamed at `/audio/{pid}`; cover at `/cover/{pid}.jpg`.
- **404 contract**: episodes that are `SERVED` (or missing from disk) must return HTTP 404 on `/audio/{pid}` and `/cover/{pid}.jpg` — this contract is unchanged by EPIC-002.

## Epic-002 Specific Constraints (from `stories.md` US-001)
- Expiry duration is **configurable** via the existing JSON config (proposed field `expiry_days`).
- Expiry runs on a **regular interval (hourly)** alongside existing polling.
- Record of **first download time** per episode must be maintained to compute expiry.
- On expiry: move to `SERVED`, delete audio + sidecar cover, log structured JSON (pid + expiry timestamp).
- **Delete-on-download completion is removed**: the service must no longer mark an episode served / delete its file merely because a client successfully downloaded it.
