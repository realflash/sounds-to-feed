import asyncio
import logging
from pathlib import Path

from src.backend.core.config_manager import ConfigManager
from src.backend.db.state import StateManager

logger = logging.getLogger(__name__)

class Poller:
    def __init__(self, config_manager: ConfigManager, state_manager: StateManager):
        self.config_manager = config_manager
        self.state_manager = state_manager
        self.output_dir = Path("/data")

    async def poll_all(self):
        config = self.config_manager.get_config()
        for prog in config.programmes:
            await self._poll_programme(prog.name)

    async def _poll_programme(self, name: str):
        logger.info(f"Polling for programme: {name}")
        try:
            # Run get_iplayer search
            process = await asyncio.create_subprocess_exec(
                "get_iplayer",
                "--type=radio",
                f"^{name}$",
                "--listformat=<pid>|<name>|<episode>|<desc>|<firstbcast>",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"get_iplayer search failed for {name}: {stderr.decode()}")
                return

            lines = stdout.decode().splitlines()
            for line in lines:
                parts = line.split("|")
                # Look for lines that start with an 8-character PID
                if len(parts) >= 3 and len(parts[0]) == 8 and parts[0].isalnum():
                    pid = parts[0]
                    prog_name = parts[1]
                    episode = parts[2]
                    
                    episode_data = self.state_manager.get_episode(pid)
                    if episode_data:
                        if episode_data['status'] == "SERVED":
                            logger.debug(f"Skipping {pid} (already served)")
                            continue
                        if episode_data['status'] == "DOWNLOADED":
                            filename = episode_data['filename']
                            if filename and Path(filename).exists():
                                logger.debug(f"Skipping {pid} (already downloaded and exists)")
                                continue
                            else:
                                logger.warning(
                                    f"Episode {pid} marked as DOWNLOADED but file missing. "
                                    "Re-downloading."
                                )
                    
                    logger.info(f"Downloading new episode {pid} for {name}")
                    await self._download_episode(pid, prog_name, episode)
        except Exception as e:
            logger.error(f"Error polling programme {name}: {e}")

    async def _download_episode(self, pid: str, prog_name: str, episode: str):
        # We use a safe filename prefix without spaces
        safe_name = prog_name.replace(" ", "_").replace("/", "_")
        safe_episode = episode.replace(" ", "_").replace("/", "_")
        file_prefix = f"{pid}_{safe_name}_{safe_episode}"
        
        try:
            process = await asyncio.create_subprocess_exec(
                "get_iplayer", "--type=radio", "--pid", pid, "--get", "--force",
                "--file-prefix", file_prefix, "--output", str(self.output_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"Failed to download episode {pid}: {stderr.decode()}")
                return
                
            # Find the downloaded file
            # get_iplayer typically creates a .m4a file for radio
            expected_file = self.output_dir / f"{file_prefix}.m4a"
            if expected_file.exists():
                self.state_manager.mark_downloaded(pid, str(expected_file))
                logger.info(f"Successfully downloaded {pid} to {expected_file}")
            else:
                # If it didn't create exactly that file, let's search for any matching file

                matching_files = list(self.output_dir.glob(f"{file_prefix}*"))
                if matching_files:
                    self.state_manager.mark_downloaded(pid, str(matching_files[0]))
                    logger.info(f"Successfully downloaded {pid} to {matching_files[0]}")
                else:
                    logger.error(f"Download command succeeded but output file not found for {pid}")
                    
        except Exception as e:
            logger.error(f"Exception during download of {pid}: {e}")
