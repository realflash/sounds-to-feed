# Sounds to Feed

Sounds to Feed is a Python 3.12 service designed to periodically poll and download BBC Radio programmes using `get_iplayer`, and dynamically expose them as a standardized podcast RSS feed compatible with mobile podcast players like AntennaPod.

> [!WARNING]
> **Single User Constraints**:
> This service is strictly designed for a **single user** setup:
> - **One Configuration**: Programmed via a single configuration file.
> - **One Feed**: Exposes a single, unified podcast RSS feed (`/feed.xml`).
> - **One Client**: Designed to be consumed by exactly one client podcast player. 
> 
> Once the first client successfully downloads an episode, the file is considered "served" and is immediately deleted from the filesystem (if `delete_on_download` is enabled). Any subsequent attempts to download the same episode will fail (HTTP 404).

---

## Architecture Overview

1. **Background Poller**: Periodically fetches and parses the BBC RMS API to find new episodes matching configured programmes, invokes `get_iplayer` to download them to a local directory, and extracts cover art to sidecar `.jpg` files.
2. **FastAPI Web Server**: Serves a dynamic, AntennaPod-compatible podcast feed at `/feed.xml`, streams `.m4a` audio files at `/audio/{pid}`, and serves dynamic cover art at `/cover/{pid}.jpg`.
3. **Lifecycle State Management**: Uses a local SQLite database (`state.db` under `/data`) to track the status of downloaded and served episodes.
4. **Delete-on-Download**: Once an episode's audio file has been successfully streamed/downloaded by a client, the service automatically deletes the audio file and its sidecar cover art from disk to conserve space (if `delete_on_download` is enabled in config).

---

## Getting Started

### Prerequisites
- Python 3.12
- `uv` (for package management)
- `get_iplayer` (with Perl dependencies, required for local downloading)
- Docker (for containerized runs)

---

## Configuration

The application reads its configuration from `config/config.json` (or `/config/config.json` inside the container).

Example structure:
```json
{
  "global_config": {
    "delete_on_download": true,
    "output_dir": "/data"
  },
  "programmes": [
    {
      "name": "Business Daily",
      "start_from_date": "2026-04-01",
      "display_name": "Biz Daily"
    },
    {
      "name": "Cautionary Tales with Tim Harford",
      "start_from_date": "2026-04-01"
    }
  ]
}
```

- **`delete_on_download`**: Delete audio and cover files once successfully served to a client.
- **`programmes`**: A list of programmes to poll.
  - **`name`**: The exact programme name as known to `get_iplayer`.
  - **`start_from_date`**: (Optional) Filter out episodes broadcast before this date (ISO format `YYYY-MM-DD`).
  - **`display_name`**: (Optional) Friendly override title for the podcast feed.

---

## Running Locally

### 1. Local Python Service
Ensure you have package dependencies installed via `uv`:
```bash
# Sync virtual environment
uv sync
```

To run the FastAPI server with auto-reload:
```bash
make dev
```
The application will start on `http://localhost:8000`.

### 2. Using Docker Compose
You can run the application container locally with mounted directories:
```bash
docker-compose up --build
```
This mounts the `./data` and `./config` directories for persistent storage and configuration.

### 3. Using Launch Script
Alternatively, use the repository's launcher:
```bash
./run_docker.sh
```

---

## Verification & Testing

The repository uses a standard Makefile for code quality and testing:

```bash
# Format source code
make fmt

# Run linters (ruff, E, F, B, I rules)
make lint

# Run unit and integration tests (pytest)
make test
```

---

## Building & Pushing the Container

### 1. Build the Production Image
To compile the Docker container:
```bash
make build
# or run the validation-enforced build script:
./build_container.sh
```
This generates `sounds-to-feed-app:latest` using a multi-stage distroless base containing Python 3.12 and `get_iplayer`.

### 2. Tag and Push to Private Registry
A template script is provided to push images to DigitalOcean Container Registry:
1. Copy `release_container_tmpl.sh` to `release_container.sh` (this file is ignored in `.gitignore`).
2. Update the registry URL inside `release_container.sh` to match your target environment.
3. Authenticate and push:
   ```bash
   doctl registry login
   ./release_container.sh [version]
   ```
