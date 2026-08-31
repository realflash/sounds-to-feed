from unittest.mock import patch

from src.backend.db.state import StateManager

# test_api.py applies a process-wide `patch(...StateManager.__init__).start()`.
# Undo it so the real constructor (which creates db_path and the schema) runs for
# these unit tests. No-op when test_api.py has not been imported.
patch.stopall()


def test_mark_downloaded_persists_downloaded_at(tmp_path):
    sm = StateManager(str(tmp_path / "state.db"))
    sm.mark_downloaded("p1", "/data/p1.m4a")
    row = sm.get_episode("p1")
    assert row["status"] == "DOWNLOADED"
    assert row["downloaded_at"] is not None
    assert row["downloaded_at"].endswith("Z")


def test_schema_migration_is_idempotent(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    sm.mark_downloaded("p1", "/data/p1.m4a")
    # Re-initialising must not raise despite the column already existing.
    sm2 = StateManager(db)
    assert sm2.get_episode("p1")["status"] == "DOWNLOADED"


def test_backfill_uses_file_mtime(tmp_path):
    db = str(tmp_path / "state.db")
    audio = tmp_path / "old.m4a"
    audio.write_bytes(b"x")
    sm = StateManager(db)
    # Simulate a pre-upgrade row inserted without downloaded_at.
    with sm._get_connection() as conn:
        conn.execute(
            "INSERT INTO episodes (pid, status, filename) VALUES (?, 'DOWNLOADED', ?)",
            ("pOld", str(audio)),
        )
        conn.commit()
    sm._init_db()  # triggers backfill
    row = sm.get_episode("pOld")
    assert row["downloaded_at"] is not None
    assert row["downloaded_at"].endswith("Z")


def test_get_expired_episodes_only_old_downloaded(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    sm.mark_downloaded("old", "/data/old.m4a")
    sm.mark_downloaded("new", "/data/new.m4a")
    with sm._get_connection() as conn:
        conn.execute(
            "UPDATE episodes SET downloaded_at = '2000-01-01T00:00:00Z' WHERE pid='old'"
        )
        conn.commit()
    sm.mark_served("new")  # already served -> excluded

    expired = sm.get_expired_episodes(7)
    pids = {row[0] for row in expired}
    assert pids == {"old"}


def test_get_expired_episodes_excludes_within_window(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    sm.mark_downloaded("recent", "/data/recent.m4a")  # downloaded_at = now

    expired = sm.get_expired_episodes(7)
    assert expired == []
