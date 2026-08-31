import logging
from datetime import datetime, timezone
from pathlib import Path

from src.backend.db.state import StateManager
from src.backend.schemas.config import GlobalConfig

logger = logging.getLogger(__name__)


class ExpiryManager:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def expire_due_episodes(self, global_config: GlobalConfig):
        expiry_days = global_config.expiry_days
        due = self.state_manager.get_expired_episodes(expiry_days)

        for pid, filename, downloaded_at in due:
            self._expire_one(pid, filename, downloaded_at)

    def _expire_one(self, pid: str, filename: str, downloaded_at: str | None):
        expiry_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        path = Path(filename)

        try:
            if path.exists():
                path.unlink()
                logger.debug(f"Deleted expired audio file {filename}")
            else:
                logger.debug(f"Expired audio file {filename} already removed")

            cover_path = path.with_suffix(".jpg")
            if cover_path.exists():
                cover_path.unlink()
                logger.debug(f"Deleted expired sidecar cover {cover_path}")
        except Exception as e:
            logger.error(f"Error deleting files for expired episode {pid}: {e}")

        # State is the source of truth: advance to SERVED even if file deletion failed.
        self.state_manager.mark_served(pid)

        logger.info(
            "Episode expired",
            extra={
                "event": "episode_expired",
                "pid": pid,
                "expiry_timestamp": expiry_timestamp,
                "downloaded_at": downloaded_at,
                "audio_file": filename,
            },
        )
