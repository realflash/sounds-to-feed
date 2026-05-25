import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from feedgen.feed import FeedGenerator
from mutagen.mp4 import MP4

from src.backend.core.config_manager import ConfigManager
from src.backend.db.state import StateManager

logger = logging.getLogger(__name__)
router = APIRouter()

def get_state_manager() -> StateManager:
    return StateManager()

def get_config_manager() -> ConfigManager:
    return ConfigManager()

@router.get("/feed.xml")
async def get_feed(
    request: Request, 
    state_manager: StateManager = Depends(get_state_manager), 
    config_manager: ConfigManager = Depends(get_config_manager)
):
    fg = FeedGenerator()
    fg.title('Sounds to Feed')
    fg.description('Downloaded get_iplayer radio programmes')
    
    base_url = str(request.base_url)
    if base_url.endswith("/"):
        base_url = base_url[:-1]
        
    fg.link(href=base_url + "/feed.xml", rel='self')
    fg.language('en')
    
    episodes = state_manager.get_downloaded_episodes()
    config = config_manager.get_config()
    
    feed_items = []
    
    for pid, filename in episodes:
        path = Path(filename)
        if not path.exists():
            continue
            
        # Find matching programme in config
        for p in config.programmes:
            safe_name = p.name.replace(" ", "_")
            prefix = f"{pid}_{safe_name}_"
            if path.stem.startswith(prefix):
                display = p.display_name if p.display_name else p.name
                episode_part = path.stem[len(prefix):].replace('_', ' ')
                title = f"{display}: {episode_part}"
                break
        else:
            # Fallback if no matching programme
            name_parts = path.stem.split("_", 2)
            if len(name_parts) >= 3:
                title = f"{name_parts[1].replace('_', ' ')}: {name_parts[2].replace('_', ' ')}"
            else:
                title = path.stem
                
        # Try to extract the original broadcast date from MP4 metadata
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo('UTC'))
        try:
            audio = MP4(str(path))
            if '©day' in audio.tags and audio.tags['©day']:
                day_str = audio.tags['©day'][0]
                # parse '2026-05-20T00:00:00Z'
                parsed_date = datetime.fromisoformat(day_str.replace('Z', '+00:00'))
                mtime = parsed_date
        except Exception as e:
            logger.warning(f"Could not extract date from {filename}: {e}")
            
        feed_items.append({
            'pid': pid,
            'title': title,
            'path': path,
            'mtime': mtime,
        })
        
    # Sort items by mtime descending (newest first)
    feed_items.sort(key=lambda x: x['mtime'], reverse=False)
    
    for item in feed_items:
        fe = fg.add_entry()
        fe.id(item['pid'])
        fe.title(item['title'])
        
        audio_url = base_url + f"/audio/{item['pid']}"
        file_size = str(item['path'].stat().st_size)
        fe.enclosure(audio_url, file_size, 'audio/mp4')
        fe.pubDate(item['mtime'])
        
    rss_feed = fg.rss_str(pretty=True)
    return Response(content=rss_feed, media_type="application/xml")
