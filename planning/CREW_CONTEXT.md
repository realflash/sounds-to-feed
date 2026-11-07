# Crew context (auto-generated; hash: 074170c35ccda628)

Product: attono-blueprint-app (requires-python >=3.12)
Dependencies: fastapi>=0.110.0, uvicorn>=0.34.0, python-json-logger>=2.0.7, feedgen>=1.0.0, starlette>=1.3.1, mutagen>=1.47.0, httpx>=0.28.1, anyio>=4.14.2 ...
Make targets: build, build-container, clean, code-scan, container-scan, dev, fmt, fmt-backend, help, info, lint, lint-backend, test, test-backend
Backend tests: 8 test files under app/src/backend/tests

Build pipeline (build.sh -> build_container.sh):
- Docker-free stages, run here: lint, the whole test suite, and the code scan (pip-audit, bandit, semgrep, trivy config).
- Docker stages, run by the trusted builder (not here): container build and container image scan.
- Product standards live in /workspace/product_standards (base image and blueprints).
