# Design: EPIC-002 Time-based Expiry

## Problem & Approach

The current "mark served on download" strategy (EPIC-001 US-004) deletes an episode's file and
marks it `SERVED` the moment a client successfully downloads it. In practice this breaks the
client's own re-attempt/retry behaviour: gaps appear in the episode list because the file is gone
before the client is certain it has the complete download.

EPIC-002 replaces that trigger with **time-based expiry**: an episode stays `DOWNLOADED` (and thus
available in the feed and on disk) for a configurable `expiry_days` window measured from its first
download, after which it is moved to `SERVED` and deleted. This decouples deletion from the
client's download completion signal entirely.

## Architecture Overview

No new services or processes. The change is contained within the existing constant-running service:
a new `ExpiryManager` runs inside the existing hourly loop in `main.py`, alongside `Poller`. State
schema and config schema gain one new field each. The download-completion deletion path in
`audio.py` is removed.

```
                 ┌────────────────── hourly loop (main.py: polling_task) ──────────────────┐
                 │                                                                          │
   config.json ──┤  ConfigManager.load_config()  ──► Poller.poll_all()                       │
   (expiry_days) │                                   ExpiryManager.expire_due_episodes()    │
                 └──────────────────────────────────────────────────────────────────────────┘
                                      │                                   │
                                      ▼                                   ▼
                          state.db: episodes                 filesystem: /data/*.m4a + *.jpg
                          (status, downloaded_at)            (deleted on expiry)
```

## Components

### 1. Config Schema Extension — `schemas/config.py` (Standard: JSON re-read, configurable)
- Add `expiry_days: int = 7` to `GlobalConfig` (backwards compatible: existing configs without the
  field keep the 7-day default). Adheres to *Config Management* standard — re-read live each cycle.
- `delete_on_download` is retained in the model for backwards compatibility but is **no longer
  used** by the new behaviour (see Component 4). Documented as deprecated; deletion is now driven
  solely by expiry.

### 2. State Schema Extension — `db/state.py` (Standard: additive migration, SQLite at /data)
- Add column `downloaded_at TEXT` to `episodes` via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS
  downloaded_at TEXT` (additive; safe in-place upgrade).
- **Backfill on init**: rows with `NULL downloaded_at` (downloaded before this change) are set to
  the file's modification time (`Path(filename).stat().st_mtime`, UTC) if the file exists, else
  the current UTC time. This prevents pre-upgrade episodes from expiring instantly.
- Update `mark_downloaded(pid, filename)` to also persist `downloaded_at = <now UTC ISO8601>`.
- Add `get_expired_episodes(expiry_days: int)` → returns `pid, filename` for rows where
  `status = 'DOWNLOADED'` and `downloaded_at <= now - expiry_days`. Uses UTC consistently.
- `mark_served(pid)` unchanged (still the terminal state).

### 3. ExpiryManager — new `core/expiry.py` (Standard: hourly interval, JSON logging, non-root fs)
- `expire_due_episodes(config: GlobalConfig, state_manager: StateManager)`:
  1. Read `expiry_days` from the **current** config (live reload respected).
  2. For each row from `get_expired_episodes(expiry_days)`:
     - Delete the audio file (`Path(filename).unlink(missing_ok=True)`).
     - Delete the sidecar cover (`Path(filename).with_suffix(".jpg").unlink(missing_ok=True)`).
     - `state_manager.mark_served(pid)`.
     - Emit a structured JSON log: `{"event": "episode_expired", "pid": ..., "expiry_timestamp": <UTC ISO8601>, "downloaded_at": ..., "filename": ...}` — adheres to *Logging* standard (`json_ensure_ascii=False`).
- Failures deleting a file are logged as errors but do **not** block marking `SERVED` (state is the
  source of truth; a missing file is already effectively served).

### 4. Remove Download-Completion Deletion — `api/audio.py` (Standard: 404 contract unchanged)
- `serve_audio` no longer schedules a background delete / `mark_served` on successful client
  download. It simply streams the file (status stays `DOWNLOADED`, file stays on disk until expiry).
- `delete_audio_file` helper and the `delete_on_download` branch are removed.
- The 404 contract is preserved: `SERVED` or missing-file episodes still return 404 on `/audio/{pid}`
  and `/cover/{pid}.jpg` (no change to `feed.py` filtering — it already lists only `DOWNLOADED`).

### 5. Scheduling — `main.py` (Standard: constant service, hourly)
- Inside `polling_task`, after `await poller.poll_all()` each hour, call
  `ExpiryManager(...).expire_due_episodes(config_manager.get_config().global_config, state_manager)`.
- Keeps a single hourly cadence as required; no new thread/task needed.

## Edge Cases & Risks
- **Pre-upgrade episodes** (no `downloaded_at`): backfilled from file mtime so they expire relative
  to their real download time, not immediately.
- **`expiry_days` change at runtime**: read fresh each cycle via live config reload.
- **Concurrent download + expiry**: expiry only acts on `DOWNLOADED` rows; a row being downloaded
  this same cycle will have a recent `downloaded_at` and won't be eligible.
- **File already gone**: logged, state still advanced to `SERVED`.
- **`expiry_days = 0`**: would expire everything immediately; treat `<= 0` as "expire immediately"
  is acceptable but should be documented; default 7 avoids accidental data loss.
