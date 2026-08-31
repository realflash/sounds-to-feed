import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from mutagen.mp4 import MP4

from src.backend.core.config_manager import ConfigManager
from src.backend.db.state import StateManager

logger = logging.getLogger(__name__)
router = APIRouter()


def get_state_manager() -> StateManager:
    return StateManager()


def get_config_manager() -> ConfigManager:
    return ConfigManager()


@router.get("/audio/{pid}")
async def serve_audio(
    pid: str,
    state_manager: StateManager = Depends(get_state_manager),
):
    # EPIC-002: the episode is NOT marked served / deleted on client download. It
    # remains DOWNLOADED and on disk until the hourly ExpiryManager retires it.
    episode = state_manager.get_episode(pid)
    if not episode or episode["status"] != "DOWNLOADED":
        raise HTTPException(status_code=404, detail="Audio not found")

    filename = episode.get("filename")
    if not filename or not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Audio file missing from disk")

    return FileResponse(path=filename, media_type="audio/mp4", filename=Path(filename).name)


@router.get("/cover/{pid}.jpg")
async def serve_cover(pid: str, state_manager: StateManager = Depends(get_state_manager)):
    episode = state_manager.get_episode(pid)
    if not episode or episode["status"] != "DOWNLOADED":
        raise HTTPException(status_code=404, detail="Audio not found")

    filename = episode.get("filename")
    if not filename:
        raise HTTPException(status_code=404, detail="Audio file path missing")

    path = Path(filename)
    cover_path = path.with_suffix(".jpg")

    # If sidecar cover file exists, serve it
    if cover_path.exists():
        return Response(content=cover_path.read_bytes(), media_type="image/jpeg")

    # If the .m4a file exists, dynamically extract and save cover
    if path.exists():
        try:
            from mutagen.mp4 import MP4Cover

            audio = MP4(str(path))
            if "covr" in audio.tags and audio.tags["covr"]:
                covr = audio.tags["covr"][0]
                media_type = "image/jpeg"
                if hasattr(covr, "imageformat") and covr.imageformat == MP4Cover.FORMAT_PNG:
                    media_type = "image/png"

                # Write the sidecar jpg file for subsequent requests
                cover_path.write_bytes(bytes(covr))
                logger.info(f"Dynamically extracted and saved sidecar cover to {cover_path}")
                return Response(content=bytes(covr), media_type=media_type)
        except Exception as e:
            logger.error(f"Error extracting cover art from {filename}: {e}")

    raise HTTPException(status_code=404, detail="Cover art not found")
