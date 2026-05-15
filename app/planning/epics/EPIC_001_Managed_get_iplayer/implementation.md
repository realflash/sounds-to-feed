# Implementation Plan: EPIC-001

## Phase 1: Container and Infrastructure
1. **Dockerfile**: Create a multi-stage Dockerfile that installs `get_iplayer` (and its Perl dependencies) and Python 3.12, targeting a distroless runtime.
2. **Docker Compose**: Add a `docker-compose.yml` for local development, mounting the config volume and download directory.

## Phase 2: Core Service and Config
1. **ConfigManager**: Implement Python class to read and parse the `config.json`.
2. **Scheduler**: Implement the hourly polling loop using `asyncio`.
3. **Logging**: Setup JSON structured logging using `python-json-logger`.

## Phase 3: Downloader
1. **get_iplayer Integration**: Implement a wrapper class to invoke `get_iplayer` with the correct arguments (e.g., `--type=radio`, `--get`, `--file-prefix`).
2. **State Tracking**: Implement logic to track what has been downloaded and deleted, ensuring compliance with US-002 rules regarding re-downloading.

## Phase 4: Podcast Server
1. **FastAPI Server**: Create the web server using FastAPI.
2. **RSS Generation**: Implement the endpoint to build the podcast XML based on the downloaded files, ensuring AntennaPod compatibility.
3. **File Serving & Deletion**: Implement the endpoint to serve the audio files, with the custom logic to delete the file after a successful stream if `delete_on_download` is enabled.
