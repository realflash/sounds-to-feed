import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _file_mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


class StateManager:
    def __init__(self, db_path: str = "/data/state.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    pid TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    filename TEXT
                )
            """)

            # EPIC-002: additively add the first-download timestamp column so the
            # schema upgrade is safe on existing state.db files.
            cursor.execute("PRAGMA table_info(episodes)")
            columns = {row[1] for row in cursor.fetchall()}
            if "downloaded_at" not in columns:
                cursor.execute("ALTER TABLE episodes ADD COLUMN downloaded_at TEXT")

            conn.commit()

        self._backfill_downloaded_at()

    def _backfill_downloaded_at(self):
        # Pre-upgrade rows have no downloaded_at. Derive it from the file's mtime so
        # they expire relative to their real download time rather than immediately.
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pid, filename FROM episodes "
                "WHERE downloaded_at IS NULL AND filename IS NOT NULL"
            )
            rows = cursor.fetchall()
            now = _utc_now_iso()
            for pid, filename in rows:
                ts = now
                path = Path(filename)
                if path.exists():
                    try:
                        ts = _file_mtime_iso(path)
                    except OSError:
                        ts = now
                cursor.execute(
                    "UPDATE episodes SET downloaded_at = ? WHERE pid = ?", (ts, pid)
                )
            conn.commit()

    def mark_downloaded(self, pid: str, filename: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO episodes (pid, status, filename, downloaded_at)
                VALUES (?, 'DOWNLOADED', ?, ?)
                ON CONFLICT(pid) DO UPDATE SET
                    status='DOWNLOADED',
                    filename=excluded.filename,
                    downloaded_at=excluded.downloaded_at
            """,
                (pid, filename, _utc_now_iso()),
            )
            conn.commit()
            logger.info(f"Marked episode {pid} as DOWNLOADED")

    def mark_served(self, pid: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE episodes
                SET status = 'SERVED'
                WHERE pid = ?
            """,
                (pid,),
            )
            conn.commit()
            logger.info(f"Marked episode {pid} as SERVED")

    def get_status(self, pid: str) -> str | None:
        row = self.get_episode(pid)
        return row["status"] if row else None

    def get_episode(self, pid: str) -> dict | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, filename, downloaded_at FROM episodes WHERE pid = ?", (pid,)
            )
            row = cursor.fetchone()
            if row:
                return {"status": row[0], "filename": row[1], "downloaded_at": row[2]}
            return None

    def get_downloaded_episodes(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pid, filename FROM episodes WHERE status = 'DOWNLOADED'")
            return cursor.fetchall()

    def get_expired_episodes(self, expiry_days: int):
        threshold = (
            datetime.now(timezone.utc) - timedelta(days=expiry_days)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Zero-padded UTC ISO8601 strings sort lexicographically, so a string
            # comparison correctly selects rows older than the expiry threshold.
            cursor.execute(
                "SELECT pid, filename, downloaded_at FROM episodes "
                "WHERE status = 'DOWNLOADED' "
                "AND downloaded_at IS NOT NULL "
                "AND downloaded_at <= ?",
                (threshold,),
            )
            return cursor.fetchall()
