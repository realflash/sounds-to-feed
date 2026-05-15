# Epic Standards: EPIC-001 Managed get_iplayer

## Inviolable Rules

### Python & Backend
- **Python Version**: 3.12 (from `ruff.toml` and `pyproject.toml`)
- **Package Management**: `uv` (from `Makefile` and `Dockerfile`)
- **Linting & Formatting**: `ruff` with line length 100, targeting py312. Selected rules: E, F, I, B, UP, N. Ignored rules: B008 (from `ruff.toml` and `pyproject.toml`).
- **Dependencies**: Use `uv` and `pyproject.toml` for managing dependencies.

### Container & Infrastructure
- **Base Image Constraint**: The container must be distroless (explicit requirement in US-001).
- **Service Design**: The service must run constantly, polling every hour without terminating.
- **Config Management**: JSON file mounted as a volume. Changes re-read on poll without container rebuild.
- **Logging**: Structured JSON logging to the console.

### API & Output
- **Podcast Feed**: Served over HTTP, port defined via environment variable. Format compatible with AntennaPod (Android).
- **Metadata**: Embedded into the podcast feed.
