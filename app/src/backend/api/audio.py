import logging
import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from src.backend.core.config_manager import ConfigManager
from src.backend.db.state import StateManager

logger = logging.getLogger(__name__)
router = APIRouter()

def get_state_manager() -> StateManager:
    return StateManager()

def get_config_manager() -> ConfigManager:
    return ConfigManager()

def delete_audio_file(pid: str, filename: str, state_manager: StateManager):
    logger.info(f"Background task: deleting audio file for {pid}")
    try:
        path = Path(filename)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted file {filename}")
        else:
            logger.warning(f"File {filename} already deleted or not found")
        
        state_manager.mark_served(pid)
    except Exception as e:
        logger.error(f"Error in background delete task for {pid}: {e}")

@router.get("/audio/{pid}")
async def serve_audio(
    pid: str, 
    background_tasks: BackgroundTasks,
    state_manager: StateManager = Depends(get_state_manager),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    episode = state_manager.get_episode(pid)
    if not episode or episode['status'] != "DOWNLOADED":
        raise HTTPException(status_code=404, detail="Audio not found")

    filename = episode.get('filename')
    if not filename or not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Audio file missing from disk")

    config = config_manager.get_config()
    
    if config.global_config.delete_on_download:
        background_tasks.add_task(delete_audio_file, pid, filename, state_manager)
        
    return FileResponse(path=filename, media_type="audio/mp4", filename=Path(filename).name)
