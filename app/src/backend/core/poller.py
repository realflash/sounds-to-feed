import asyncio
import logging
import os
import urllib.parse
from pathlib import Path

import httpx

from src.backend.core.config_manager import ConfigManager
from src.backend.db.state import StateManager
from src.backend.schemas.config import ProgrammeConfig

logger = logging.getLogger(__name__)

class Poller:
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config_manager = config_manager
        self.state_manager = state_manager

    async def poll_all(self):
        config = self.config_manager.get_config()
        for prog in config.programmes:
            await self._poll_programme(prog)

    async def _poll_programme(self, prog: ProgrammeConfig):
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
                        urn = episode.get('urn', '')
                        if 'episode:' in urn:
                            pid = urn.split('episode:')[-1]
                        else:
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
            logger.error(f"Error polling programme {name}: {e}")

    async def _download_episode(self, pid: str, prog_name: str, episode: str):
        import re
        # We use a safe filename prefix without spaces
        raw_prefix = f"{pid}_{prog_name}_{episode}".replace(" ", "_")
        # Sanitize file prefix to avoid Wide character error in get_iplayer's decode_fs
        file_prefix = re.sub(r'[^A-Za-z0-9_\-]', '', raw_prefix).replace("/", "_")
        
        output_dir = Path(self.config_manager.get_config().global_config.output_dir)
        
        try:
            env = os.environ.copy()
            env["LANG"] = "C.UTF-8"
            env["LC_ALL"] = "C.UTF-8"

            cmd = [
                "get_iplayer", 
                "--encoding-locale=UTF-8", 
                "--encoding-locale-fs=UTF-8", 
                "--encoding-console-out=UTF-8",
                "--type=radio", "--pid", pid, "--get", "--force",
                "--file-prefix", file_prefix, "--output", str(output_dir)
            ]
            logger.debug(f"Executing download command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            async def stream_to_logger(stream, prefix):
                async for line in stream:
                    decoded = line.decode('utf-8', errors='replace').strip()
                    if decoded:
                        logger.debug(f"{prefix} {decoded}")

            await asyncio.gather(
                stream_to_logger(process.stdout, f"[get_iplayer {pid} stdout]"),
                stream_to_logger(process.stderr, f"[get_iplayer {pid} stderr]")
            )
            
            await process.wait()
            
            if process.returncode != 0:
                logger.error(f"Failed to download episode {pid} with code {process.returncode}")
                return
                
            # Find the downloaded file
            # get_iplayer typically creates a .m4a file for radio
            expected_file = output_dir / f"{file_prefix}.m4a"
            if expected_file.exists():
                self.state_manager.mark_downloaded(pid, str(expected_file))
                logger.info(f"Successfully downloaded {pid} to {expected_file}")
            else:
                # If it didn't create exactly that file, let's search for any matching file

                matching_files = list(output_dir.glob(f"{file_prefix}*"))
                if matching_files:
                    self.state_manager.mark_downloaded(pid, str(matching_files[0]))
                    logger.info(f"Successfully downloaded {pid} to {matching_files[0]}")
                else:
                    logger.error(f"Download command succeeded but output file not found for {pid}")
                    
        except Exception as e:
            logger.error(f"Exception during download of {pid}: {e}")
