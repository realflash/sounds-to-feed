import re

with open("src/backend/core/poller.py", "r") as f:
    content = f.read()

# We will replace _poll_programme method
new_poll_programme = """    async def _poll_programme(self, prog: ProgrammeConfig):
        import urllib.parse
        import httpx
        from datetime import datetime
        
        name = prog.name
        logger.info(f"Polling for programme: {name}")
        
        try:
            # 1. Search for the brand ID
            query = urllib.parse.quote(name)
            search_url = f"https://rms.api.bbc.co.uk/v2/experience/inline/search?q={query}"
            
            async with httpx.AsyncClient() as client:
                search_response = await client.get(search_url)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                brand_id = None
                for item in search_data.get('data', []):
                    for entry in item.get('data', []):
                        if entry.get('type') == 'playable_item':
                            container = entry.get('container', {})
                            if container.get('title', '').lower() == name.lower():
                                brand_id = container.get('id')
                                break
                    if brand_id:
                        break
                        
                if not brand_id:
                    logger.error(f"Could not find brand ID for programme {name}")
                    return
                    
                logger.debug(f"Found brand ID {brand_id} for {name}")
                
                # 2. Fetch episodes with pagination
                limit = 100
                offset = 0
                has_more = True
                
                while has_more:
                    episodes_url = f"https://rms.api.bbc.co.uk/v2/programmes/playable?container={brand_id}&sort=recent&type=episode&limit={limit}&offset={offset}"
                    episodes_response = await client.get(episodes_url)
                    episodes_response.raise_for_status()
                    episodes_data = episodes_response.json()
                    
                    items = episodes_data.get('data', [])
                    if not items:
                        break
                        
                    for episode in items:
                        pid = episode.get('id')
                        prog_name = name
                        titles = episode.get('titles', {})
                        ep_title = titles.get('secondary', titles.get('primary', pid))
                        
                        release_date = episode.get('release', {}).get('date', '')
                        
                        if prog.start_from_date and release_date:
                            # release_date is ISO8601 string, e.g., '2026-04-13T00:00:00Z'
                            if release_date[:10] < prog.start_from_date:
                                logger.debug(
                                    f"Skipping {pid} (published {release_date} "
                                    f"before start_from_date {prog.start_from_date})"
                                )
                                # Since sort=recent, older items follow. We could break here, but
                                # continuing is safer in case sorting is slightly off.
                                continue
                                
                        episode_data = self.state_manager.get_episode(pid)
                        if episode_data:
                            if episode_data['status'] == "SERVED":
                                logger.debug(f"Skipping {pid} (already served)")
                                continue
                            if episode_data['status'] == "DOWNLOADED":
                                filename = episode_data.get('filename')
                                if filename and Path(filename).exists():
                                    logger.debug(f"Skipping {pid} (already downloaded and exists)")
                                    continue
                                else:
                                    logger.warning(
                                        f"Episode {pid} marked as DOWNLOADED but file missing. "
                                        "Re-downloading."
                                    )
                        
                        logger.info(
                            f"Downloading new episode {pid} for {name} (published: {release_date})"
                        )
                        await self._download_episode(pid, prog_name, ep_title)
                        
                    offset += limit
                    # If we fetched fewer than limit items, we've reached the end
                    if len(items) < limit:
                        has_more = False
                        
        except Exception as e:
            logger.error(f"Error polling programme {name}: {e}")"""

# Regex replacement
content_new = re.sub(
    r'    async def _poll_programme\(self, prog: ProgrammeConfig\):.*?(?=    async def _download_episode)',
    new_poll_programme + '\n\n',
    content,
    flags=re.DOTALL
)

with open("src/backend/core/poller.py", "w") as f:
    f.write(content_new)

print("Updated poller.py")
