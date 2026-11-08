# Sounds to Feed

Sounds to Feed is a Python service (current-stable Debian + Python 3.13, provided by the Attono standard base image) designed to periodically poll and download BBC Radio programmes using `get_iplayer`, and dynamically expose them as a standardized podcast RSS feed compatible with mobile podcast players like AntennaPod.

> [!WARNING]
> **Single User Constraints**:
> This service is strictly designed for a **single user** setup:
> - **One Configuration**: Programmed via a single configuration file.
> - **One Feed**: Exposes a single, unified podcast RSS feed (`/feed.xml`).
> - **One Client**: Designed to be consumed by exactly one client podcast player. 
> 
> Episodes are retained on disk for a configurable `expiry_days` window (default 7 days) measured from their first download, after which they are automatically expired: moved to a "served" state and deleted from the filesystem. Once an episode is expired, any subsequent attempt to download it will fail (HTTP 404). This decouples deletion from the client's download behaviour, so a client can safely re-request an episode within its window.

---

## Architecture Overview

1. **Background Poller**: Periodically fetches and parses the BBC RMS API to find new episodes matching configured programmes, invokes `get_iplayer` to download them to a local directory, and extracts cover art to sidecar `.jpg` files.
2. **FastAPI Web Server**: Serves a dynamic, AntennaPod-compatible podcast feed at `/feed.xml`, streams `.m4a` audio files at `/audio/{pid}`, and serves dynamic cover art at `/cover/{pid}.jpg`.
3. **Lifecycle State Management**: Uses a local SQLite database (`state.db` under `/data`) to track the status of downloaded and served episodes, including the timestamp of each episode's first download.
4. **Time-based Expiry**: A background expiry task (running hourly alongside polling) retires episodes once they are older than the configured `expiry_days` window. The age is measured from the episode's first download (its download date, recorded as `downloaded_at` in the state database), **not** from the programme's publish/broadcast date. An expired episode is moved to a "served" state and its audio file and sidecar cover art are deleted from disk to conserve space. Expiry events are logged in structured JSON (including the episode ID and expiry timestamp).

---

## Getting Started

### Prerequisites
- Python 3.13 (current-stable, provided in-container by the standard base image; the tooling does not pin a Python minor version)
- A Python 3 venv module — required so `pip-audit` can build an isolated environment when running `make code-scan`
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
    "expiry_days": 7,
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

- **`expiry_days`**: Number of days an episode is retained after its first download before being automatically expired (moved to "served" and deleted). Defaults to `7`. Changing this value takes effect on the next poll cycle without a rebuild.
- **`delete_on_download`**: *Deprecated.* Episodes are no longer deleted based on a client successfully downloading them; retention is now governed entirely by `expiry_days`. The field is retained only for backwards compatibility with existing config files.
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
This generates `sounds-to-feed-app:latest` from `registry.digitalocean.com/attono/attono-base:latest`
(locally `attono-base`), the company-standard base image. That base ships current-stable
Debian + Python 3.13, Node/npm, `uv`, and `attono-harden`; it is intentionally rolling
(`:latest`), so freshness comes for free. Pin by image **digest** if you need a
byte-reproducible build; the exact component versions are recorded inside the image at
`/attono/manifest.json`.

The Dockerfile follows the standard two-stage pattern (`/workspace/product_standards/base/README.md`):

- **`FROM registry.digitalocean.com/attono/attono-base:latest AS deps`** — the only stage with a
  shell + package manager. Product-specific tooling (`perl` plus `libxml-simple-perl`,
  `liblwp-protocol-https-perl`, `libmojolicious-perl`, `libcgi-pm-perl`, `ffmpeg`,
  `atomicparsley`, `ca-certificates`) and a **pinned** `get_iplayer` release (e.g. `v3.36`, not
  `master`) are installed here, then Python deps are installed into the base's system Python.
  Each product component and the reason for its pin is appended to `/attono/manifest.json`.
- **`FROM deps` + `RUN /usr/local/bin/attono-harden`** — the final image *is* the dependency
  stage, hardened **in place**. Because the full filesystem is inherited, the `.so`
  dependencies of every product tool carry into the final image automatically; you never
  enumerate libraries and you never `COPY --from=` a pre-hardened base. After hardening there
  is no shell/apt/curl/wget, so the `ENTRYPOINT` is a JSON array (`["python", "-m",
  "src.backend.main"]`) — never shell-form.

No hardcoded Python minor version paths (no `/usr/local/lib/python3.12/...`), no
`gcr.io/distroless/*`, no `python:3.12-slim`, and no `debian:12-slim`/`uv` builder as the
final image. The app is a normal, self-contained runtime service, so it fits the standard
**Scenario A/B** pattern with no exception required — **no Scenario D exemption is needed**.

### 2. Tag and Push to Private Registry
A template script is provided to push images to DigitalOcean Container Registry:
1. Copy `release_container_tmpl.sh` to `release_container.sh` (this file is ignored in `.gitignore`).
2. Update the registry URL inside `release_container.sh` to match your target environment.
3. Authenticate and push:
   ```bash
   doctl registry login
   ./release_container.sh [version]
   ```
