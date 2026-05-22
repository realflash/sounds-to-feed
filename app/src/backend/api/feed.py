import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from feedgen.feed import FeedGenerator

from src.backend.db.state import StateManager

logger = logging.getLogger(__name__)
router = APIRouter()

def get_state_manager() -> StateManager:
    return StateManager()

@router.get("/feed.xml")
async def get_feed(request: Request, state_manager: StateManager = Depends(get_state_manager)):
    fg = FeedGenerator()
    fg.title('Sounds to Feed')
    fg.description('Downloaded get_iplayer radio programmes')
    
    base_url = str(request.base_url)
    if base_url.endswith("/"):
        base_url = base_url[:-1]
        
    fg.link(href=base_url + "/feed.xml", rel='self')
    fg.language('en')
    
    episodes = state_manager.get_downloaded_episodes()
    
    for pid, filename in episodes:
        path = Path(filename)
        if not path.exists():
            continue
            
        fe = fg.add_entry()
        fe.id(pid)
        
        name_parts = path.stem.split("_", 2)
        if len(name_parts) >= 3:
            title = f"{name_parts[1].replace('_', ' ')}: {name_parts[2].replace('_', ' ')}"
        else:
            title = path.stem
            
        fe.title(title)
        
        audio_url = base_url + f"/audio/{pid}"
        file_size = str(path.stat().st_size)
        fe.enclosure(audio_url, file_size, 'audio/mp4')
        
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo('UTC'))
        fe.pubDate(mtime)
        
    rss_feed = fg.rss_str(pretty=True)
    return Response(content=rss_feed, media_type="application/xml")
