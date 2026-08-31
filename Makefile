# Standard Makefile (v0.4)
# <!-- Standard Version: 0.4 -->

VERSION      := $(shell cat VERSION 2>/dev/null || echo "0.0")
BUILD_NUMBER := $(shell git rev-list --count HEAD 2>/dev/null || echo "0")
GIT_SHA      := $(shell git rev-parse --short HEAD 2>/dev/null || echo "no-git")
BUILD_TS     := $(shell date +%H%M%S)
BUILD_ID     := v$(VERSION).b$(BUILD_NUMBER)-$(GIT_SHA)-$(BUILD_TS)

.PHONY: help fmt lint test build clean info

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

info: ## Show build information
	@echo "Build ID: $(BUILD_ID)"

# Handle uv availability
UV := $(shell if command -v uv >/dev/null 2>&1; then echo uv; elif [ -f ~/.local/bin/uv ]; then echo ~/.local/bin/uv; else echo uv; fi)
RUN_UV := $(UV) run

fmt: fmt-backend ## Format all source code

fmt-backend: ## Format web source code
	$(RUN_UV) ruff format app/src/backend

lint: lint-backend ## Run all static analysis

lint-backend: ## Run web static analysis
	cd app && PYTHONPATH=. $(RUN_UV) ruff check src/backend

code-scan: ## Run source-level security scanners
	@echo "Running Source Code Security Scans..."
	cd app && uv export --no-dev --format requirements-txt | uv run pip-audit -r /dev/stdin
	cd app && uv run bandit -c pyproject.toml -r src/backend
	docker run --rm -v $(PWD):/src returntocorp/semgrep semgrep --config auto /src --error

container-scan: ## Run container vulnerability scanner
	@echo "Running Container Security Scan..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(HOME)/.cache:/root/.cache/ \
		aquasec/trivy image --exit-code 1 --ignore-unfixed sounds-to-feed-app:latest

test: test-backend ## Run all unit and integration tests

test-backend: ## Run web unit and integration tests
	cd app && PYTHONPATH=. $(RUN_UV) pytest src/backend/tests/

dev: ## Run development servers
	cd app && PYTHONPATH=. uv run uvicorn src.backend.main:app --reload --port 8000

build: build-container ## Build all components for production

build-container: ## Build the docker container
	docker build --platform linux/amd64 --load --build-arg VITE_BUILD_ID=$(BUILD_ID) -t sounds-to-feed-app:latest -t sounds-to-feed-app:$(BUILD_ID) .

clean: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache
