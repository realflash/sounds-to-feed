# Testing Strategy: EPIC-002 Time-based Expiry

Goal: 100% functional coverage of EPIC-002 US-001 acceptance criteria across the testing pyramid
(unit → integration → E2E), with explicit traceability. Standards enforced: ruff rules
(E,W,F,I,B,UP,N), uv/pytest, structured JSON logging assertions, SQLite at `/data`.

## Unit Tests (fast, no I/O to real disk where mockable)
- `tests/test_config.py`
  - default `expiry_days == 7`; explicit int parsed; omitted field tolerated; non-int rejected.
- `tests/test_state.py`
  - `mark_downloaded` stores `downloaded_at` as UTC ISO8601.
  - migration `ADD COLUMN downloaded_at` is idempotent (run twice, no error).
  - backfill: pre-upgrade row (`downloaded_at IS NULL`) with an existing file gets mtime-based
    timestamp; row with missing file gets current UTC time.
  - `get_expired_episodes(expiry_days)`: returns only `DOWNLOADED` rows whose `downloaded_at` is
    older than `now - expiry_days`; excludes `SERVED`; excludes rows within the window or with
    future timestamps.
- `tests/test_expiry.py`
  - `expire_due_episodes` deletes audio file and sidecar `.jpg` (`missing_ok`).
  - calls `mark_served(pid)`.
  - emits exactly one structured JSON log line with `event=episode_expired`, `pid`, and
    `expiry_timestamp` (parse log record, assert keys + valid ISO8601).
  - recent episode (within window) is NOT expired.
  - reads `expiry_days` from the current config object (live reload).
  - a `PermissionError`/missing file during delete still results in `SERVED` state.

## Integration Tests (FastAPI TestClient / real module wiring)
- `tests/test_api.py` (extend)
  - `GET /audio/{pid}` for a `DOWNLOADED` episode returns 200, **does not delete** the file, and
    does **not** call `mark_served`; a second `GET` is still 200 (proves download-completion deletion
    removed and the original gap bug fixed). Use `DependencyOverride` + spy on `mark_served`.
  - `GET /audio/{pid}` for a `SERVED` episode still returns 404 (contract unchanged).
- `tests/test_main.py` (extend lifecycle)
  - `polling_task` calls `ExpiryManager.expire_due_episodes` once per hourly cycle, after
    `poll_all` (mock both, assert call order/count).

## End-to-End Tests (container + mock get_iplayer)
- Extend `scripts/test-docker.sh` (mirrors EPIC-001 E2E):
  - start container with mock `get_iplayer` and a mounted `config.json` including `expiry_days`.
  - assert episode appears in `/feed.xml` and is downloadable via `/audio/{pid}`.
  - re-request the audio twice → both 200 (no gaps / no premature 404).
  - advance past `expiry_days` (or set `expiry_days` small and wait one cycle) → assert episode
    removed from `/feed.xml`, file deleted from `/data`, and an `episode_expired` JSON log line
    present in container stdout.

## Traceability Matrix (US-001 → tests)
| # | Acceptance Criterion | Unit | Integration | E2E |
| - | --- | --- | --- | --- |
| 1 | Expiry after configurable duration | `test_config`, `test_expiry` | — | `test-docker.sh` (expiry_days) |
| 2 | Runs hourly alongside polling | `test_expiry` | `test_main` lifecycle | `test-docker.sh` |
| 3 | Records first-download time | `test_state` (downloaded_at + backfill) | — | `test-docker.sh` |
| 4 | On expiry → SERVED + file deleted | `test_expiry` | — | `test-docker.sh` |
| 5 | JSON log: pid + expiry timestamp | `test_expiry` (log keys) | — | `test-docker.sh` |
| 6 | Duration configurable via JSON | `test_config` | — | `test-docker.sh` |
| 7 | No longer expires on download completion | — | `test_api` (persists, 200 re-GET) | `test-docker.sh` (re-request) |

**Coverage: 7/7 functional criteria covered at E2E (100% as required by the traceability standard).**
