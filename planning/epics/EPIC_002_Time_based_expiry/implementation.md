# Implementation Plan: EPIC-002 Time-based Expiry

Phased plan enforcing the inviolable standards at each step. Each phase lists the files touched
and the standard it satisfies.

## Phase 1 — Config schema (`schemas/config.py`)
- Add `expiry_days: int = 7` to `GlobalConfig`.
- Keep `delete_on_download` field but mark it deprecated in a docstring (no longer read by the
  download path). Do not remove it to preserve config backwards-compatibility.
- *Standard: configurable JSON, live re-read (Config Management).*

## Phase 2 — State schema & backfill (`db/state.py`)
- In `_init_db`, run `ALTER TABLE episodes ADD COLUMN IF NOT EXISTS downloaded_at TEXT`.
- Add a one-time backfill: `UPDATE episodes SET downloaded_at = <file mtime UTC ISO8601> WHERE
  downloaded_at IS NULL AND filename IS NOT NULL AND <file exists>`; rows whose file is missing get
  current UTC time.
- Update `mark_downloaded` to set `downloaded_at = <now UTC ISO8601>` alongside `filename`.
- Add `get_expired_episodes(expiry_days)` returning rows where `status='DOWNLOADED'` and
  `downloaded_at <= now_utc - expiry_days` (string ISO8601 compare safe because stored in
  zero-padded UTC `YYYY-MM-DDTHH:MM:SSZ` form).
- *Standard: additive SQLite migration, /data volume, DOWNLOADED/SERVED lifecycle.*

## Phase 3 — ExpiryManager (`core/expiry.py`, new)
- Implement `ExpiryManager.expire_due_episodes(global_config, state_manager)`:
  - delete audio + sidecar `.jpg` (`missing_ok=True`),
  - `mark_served(pid)`,
  - structured JSON log with `event=episode_expired`, `pid`, `expiry_timestamp`, `downloaded_at`.
- Guard each file deletion in try/except; never let a delete error prevent `mark_served`.
- *Standard: hourly interval, JSON logging (`json_ensure_ascii=False`), non-root fs.*

## Phase 4 — Wire into hourly loop (`main.py`)
- Instantiate `ExpiryManager` once in `polling_task`.
- After `await poller.poll_all()`, call `expire_due_episodes(config_manager.get_config().global_config, state_manager)`.
- *Standard: constant service, single hourly cadence.*

## Phase 5 — Remove download-completion deletion (`api/audio.py`)
- Delete `delete_audio_file` helper and its `BackgroundTasks` usage.
- `serve_audio` streams the file unconditionally (subject to existing 404 guard for `SERVED`/missing).
- Remove the `delete_on_download` branch.
- *Standard: 404 contract unchanged; no new B008 violations.*

## Phase 6 — Docs/README (optional, low priority)
- Note in `README.md` that episode lifetime is now time-based (`expiry_days`) and the
  delete-on-download completion behaviour is replaced.

---

## Tests

### New tests (by pyramid level)
**Unit**
- `tests/test_config.py` (new): `expiry_days` defaults to 7; explicit value parsed; missing field
  tolerated; type validation rejects non-int.
- `tests/test_state.py` (new): `mark_downloaded` persists `downloaded_at`; `ADD COLUMN` migration
  is additive and idempotent; backfill sets `downloaded_at` from file mtime for pre-upgrade rows;
  `get_expired_episodes` returns only rows older than `expiry_days` and ignores `SERVED`; rows with
  `NULL`/`future` `downloaded_at` are not expired.
- `tests/test_expiry.py` (new): `expire_due_episodes` deletes audio + sidecar cover, marks `SERVED`,
  and emits a JSON log line containing `pid` and `expiry_timestamp`; recent episodes are skipped;
  uses the latest `expiry_days` from current config; a delete error still advances state to `SERVED`.

**Integration**
- Extend `tests/test_api.py`: `GET /audio/{pid}` for a `DOWNLOADED` episode now **does not delete**
  the file and does **not** mark `SERVED` — a second `GET` still returns 200 (not 404). Verifies the
  download-completion path was removed while the 404 path for `SERVED` stays.
- `tests/test_main.py` / lifecycle: hour-loop invokes expiry (mock `ExpiryManager.expire_due_episodes`
  and assert it is called once per cycle alongside `poll_all`).

**End-to-End**
- Extend `scripts/test-docker.sh` (mock `get_iplayer`): download an episode, assert it is present in
  `/feed.xml` and downloadable; set a small `expiry_days`; after the hourly expiry (or trigger a
  manual cycle) assert the episode is gone from the feed, the file is deleted from `/data`, and a
  `episode_expired` JSON log line was emitted. Also assert that *before* expiry the client can
  re-request the audio multiple times without 404 (proving the original gap bug is fixed).

### Existing tests to modify
- `tests/test_api.py::test_audio_not_downloaded`: unchanged (SERVED → 404 still valid).
- `tests/test_poller.py`: unchanged (no expiry interaction).
- `tests/conftest.py`: unchanged (StateManager/ConfigManager patched constructors still apply).

### Traceability (US-001 AC → tests)
| AC | Test(s) |
| --- | --- |
| Time-based expiry after configurable duration | `test_config`, `test_expiry`, E2E |
| Runs at regular (hourly) intervals | `test_main` lifecycle, E2E |
| Records first-download time | `test_state` (downloaded_at), backfill |
| On expiry → SERVED + file deleted | `test_expiry`, E2E |
| JSON log with pid + expiry timestamp | `test_expiry` (log assertion), E2E |
| Duration configurable via JSON | `test_config`, E2E (expiry_days) |
| No longer expires on download completion | `test_api` (file persists, 200 on re-GET) |
