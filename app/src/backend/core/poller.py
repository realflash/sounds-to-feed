import asyncio
import logging
import os
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
            env = os.environ.copy()
            env["LANG"] = "C.UTF-8"
            env["LC_ALL"] = "C.UTF-8"
            
            cmd = [
                "get_iplayer",
                "--encoding-locale=UTF-8", 
                "--encoding-locale-fs=UTF-8", 
                "--encoding-console-out=UTF-8",
                "--type=radio",
                f"^{name}$",
                "--listformat=<pid>|<name>|<episode>|<desc>|<available>"
            ]
            logger.debug(f"Executing search command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            async def read_stderr():
                async for line in process.stderr:
                    decoded = line.decode('utf-8', errors='replace').strip()
                    if decoded:
                        logger.debug(f"[get_iplayer search stderr] {decoded}")

            stdout_bytes, _ = await asyncio.gather(
                process.stdout.read(),
                read_stderr()
            )
            
            await process.wait()
            
            if process.returncode != 0:
                logger.error(f"get_iplayer search failed for {name} with code {process.returncode}")
                return

            stdout_str = stdout_bytes.decode('utf-8', errors='replace')
            lines = stdout_str.splitlines()
            for line in lines:
                parts = line.split("|")
                # Look for lines that start with an 8-character PID
                if len(parts) >= 3 and len(parts[0]) == 8 and parts[0].isalnum():
                    pid = parts[0]
                    prog_name = parts[1]
                    episode = parts[2]
                    firstbcast = parts[4] if len(parts) >= 5 else "Unknown Date"
                    
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
                    
                    logger.info(
                        f"Downloading new episode {pid} for {name} (published: {firstbcast})"
                    )
                    await self._download_episode(pid, prog_name, episode)
        except Exception as e:
            logger.error(f"Error polling programme {name}: {e}")

    async def _download_episode(self, pid: str, prog_name: str, episode: str):
        import re
        # We use a safe filename prefix without spaces
        raw_prefix = f"{pid}_{prog_name}_{episode}".replace(" ", "_")
        # Sanitize file prefix to avoid Wide character error in get_iplayer's decode_fs
        file_prefix = re.sub(r'[^A-Za-z0-9_\-]', '', raw_prefix).replace("/", "_")
        
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
                "--file-prefix", file_prefix, "--output", str(self.output_dir)
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
