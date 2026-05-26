import re

with open("app/src/backend/api/feed.py", "r") as f:
    content = f.read()

# We want to replace the iteration block:
#     for pid, filename in episodes:
#         path = Path(filename)
# ...
#         fe.pubDate(mtime)
#
# With a two-pass approach: collect, sort, then add to fg.

new_logic = """    feed_items = []
    
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
    feed_items.sort(key=lambda x: x['mtime'], reverse=True)
    
    for item in feed_items:
        fe = fg.add_entry()
        fe.id(item['pid'])
        fe.title(item['title'])
        
        audio_url = base_url + f"/audio/{item['pid']}"
        file_size = str(item['path'].stat().st_size)
        fe.enclosure(audio_url, file_size, 'audio/mp4')
        fe.pubDate(item['mtime'])"""

content = re.sub(r'    for pid, filename in episodes:.*?(?=    rss_feed = fg\.rss_str)', new_logic + '\n        \n', content, flags=re.DOTALL)

with open("app/src/backend/api/feed.py", "w") as f:
    f.write(content)

print("Updated feed.py")
