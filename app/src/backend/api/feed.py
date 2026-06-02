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
    config_manager: ConfigManager = Depends(get_config_manager),
):
    fg = FeedGenerator()
    fg.title("Sounds to Feed")
    fg.description("Downloaded get_iplayer radio programmes")

    # Load podcast extension
    fg.load_extension("podcast")
    fg.podcast.itunes_summary("Downloaded get_iplayer radio programmes")

    base_url = str(request.base_url)
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    fg.link(href=base_url + "/feed.xml", rel="self")
    fg.language("en")

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
                episode_part = path.stem[len(prefix) :].replace("_", " ")
                title = f"{display}: {episode_part}"
                break
        else:
            # Fallback if no matching programme
            name_parts = path.stem.split("_", 2)
            if len(name_parts) >= 3:
                title = f"{name_parts[1].replace('_', ' ')}: {name_parts[2].replace('_', ' ')}"
            else:
                title = path.stem

        # Try to extract the original broadcast date and metadata from MP4 metadata
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo("UTC"))
        description = None
        summary = None
        has_cover = False

        # Check if sidecar cover art exists
        if path.with_suffix(".jpg").exists():
            has_cover = True

        try:
            audio = MP4(str(path))
            if "©day" in audio.tags and audio.tags["©day"]:
                day_str = audio.tags["©day"][0]
                # parse '2026-05-20T00:00:00Z'
                parsed_date = datetime.fromisoformat(day_str.replace("Z", "+00:00"))
                mtime = parsed_date

            # Extract show notes / description
            if "©lyr" in audio.tags and audio.tags["©lyr"]:
                description = audio.tags["©lyr"][0]
            elif "©cmt" in audio.tags and audio.tags["©cmt"]:
                description = audio.tags["©cmt"][0]

            # Extract short summary / subtitle
            if "©cmt" in audio.tags and audio.tags["©cmt"]:
                summary = audio.tags["©cmt"][0]

            if "covr" in audio.tags and audio.tags["covr"]:
                has_cover = True
        except Exception as e:
            logger.warning(f"Could not extract metadata from {filename}: {e}")

        feed_items.append(
            {
                "pid": pid,
                "title": title,
                "path": path,
                "mtime": mtime,
                "description": description,
                "summary": summary,
                "has_cover": has_cover,
            }
        )

    # Sort items by mtime descending (newest first)
    feed_items.sort(key=lambda x: x["mtime"], reverse=False)

    # If there are episodes with cover art, use the latest one as the feed-level cover
    if feed_items:
        latest_with_cover = None
        for item in reversed(feed_items):
            if item["has_cover"]:
                latest_with_cover = item
                break

        if latest_with_cover:
            cover_url = base_url + f"/cover/{latest_with_cover['pid']}.jpg"
            fg.podcast.itunes_image(cover_url)

    for item in feed_items:
        fe = fg.add_entry()
        fe.id(item["pid"])
        fe.title(item["title"])

        audio_url = base_url + f"/audio/{item['pid']}"
        file_size = str(item["path"].stat().st_size)
        fe.enclosure(audio_url, file_size, "audio/mp4")
        fe.pubDate(item["mtime"])

        # Add description / show notes
        if item["description"]:
            fe.description(item["description"])

        # Add iTunes/Podcast specific elements
        if item["has_cover"]:
            cover_url = base_url + f"/cover/{item['pid']}.jpg"
            fe.podcast.itunes_image(cover_url)

        if item["summary"]:
            fe.podcast.itunes_summary(item["summary"])
            fe.podcast.itunes_subtitle(item["summary"])

    rss_feed = fg.rss_str(pretty=True)
    return Response(content=rss_feed, media_type="application/xml")
