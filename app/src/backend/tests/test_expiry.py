import logging
from unittest.mock import patch

from src.backend.core.expiry import ExpiryManager
from src.backend.db.state import StateManager
from src.backend.schemas.config import GlobalConfig

# Undo the process-wide StateManager.__init__ patch applied by test_api.py so the
# real constructor runs for these unit tests.
patch.stopall()


class _LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def _capture():
    cap = _LogCapture()
    logging.getLogger("src.backend.core.expiry").addHandler(cap)
    return cap


def test_expire_deletes_files_and_marks_served(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    audio = tmp_path / "e.m4a"
    audio.write_bytes(b"x")
    cover = tmp_path / "e.jpg"
    cover.write_bytes(b"x")
    sm.mark_downloaded("e1", str(audio))
    with sm._get_connection() as conn:
        conn.execute(
            "UPDATE episodes SET downloaded_at = '2000-01-01T00:00:00Z' WHERE pid='e1'"
        )
        conn.commit()

    cap = _capture()
    ExpiryManager(sm).expire_due_episodes(GlobalConfig(expiry_days=7))

    assert not audio.exists()
    assert not cover.exists()
    assert sm.get_status("e1") == "SERVED"

    logged = [
        r
        for r in cap.records
        if getattr(r, "event", None) == "episode_expired"
    ]
    assert len(logged) == 1
    assert logged[0].pid == "e1"
    assert getattr(logged[0], "expiry_timestamp", None)


def test_expire_skips_recent_episode(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    audio = tmp_path / "recent.m4a"
    audio.write_bytes(b"x")
    sm.mark_downloaded("r1", str(audio))  # downloaded_at = now

    ExpiryManager(sm).expire_due_episodes(GlobalConfig(expiry_days=7))

    assert audio.exists()
    assert sm.get_status("r1") == "DOWNLOADED"


def test_expire_respects_configured_expiry_days(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    audio = tmp_path / "zero.m4a"
    audio.write_bytes(b"x")
    sm.mark_downloaded("z1", str(audio))

    # expiry_days=0 -> threshold = now, freshly downloaded row is already <= now
    ExpiryManager(sm).expire_due_episodes(GlobalConfig(expiry_days=0))
    assert sm.get_status("z1") == "SERVED"
    assert not audio.exists()


def test_expire_advances_state_despite_delete_error(tmp_path):
    db = str(tmp_path / "state.db")
    sm = StateManager(db)
    # A directory at the audio path makes path.unlink() raise; state must still advance.
    d = tmp_path / "dir"
    d.mkdir()
    sm.mark_downloaded("d1", str(d))
    with sm._get_connection() as conn:
        conn.execute(
            "UPDATE episodes SET downloaded_at = '2000-01-01T00:00:00Z' WHERE pid='d1'"
        )
        conn.commit()

    ExpiryManager(sm).expire_due_episodes(GlobalConfig(expiry_days=7))
    assert sm.get_status("d1") == "SERVED"
