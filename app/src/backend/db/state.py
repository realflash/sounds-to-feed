import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodes (
                    pid TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    filename TEXT
                )
            ''')
            conn.commit()

    def mark_downloaded(self, pid: str, filename: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO episodes (pid, status, filename)
                VALUES (?, 'DOWNLOADED', ?)
                ON CONFLICT(pid) DO UPDATE SET status='DOWNLOADED', filename=excluded.filename
            ''', (pid, filename))
            conn.commit()
            logger.info(f"Marked episode {pid} as DOWNLOADED")

    def mark_served(self, pid: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE episodes
                SET status = 'SERVED'
                WHERE pid = ?
            ''', (pid,))
            conn.commit()
            logger.info(f"Marked episode {pid} as SERVED")

    def get_status(self, pid: str) -> str | None:
        row = self.get_episode(pid)
        return row['status'] if row else None

    def get_episode(self, pid: str) -> dict | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status, filename FROM episodes WHERE pid = ?', (pid,))
            row = cursor.fetchone()
            if row:
                return {'status': row[0], 'filename': row[1]}
            return None

    def get_downloaded_episodes(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pid, filename FROM episodes WHERE status = 'DOWNLOADED'")
            return cursor.fetchall()
