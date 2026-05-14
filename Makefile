# Standard Makefile (v0.4)
# <!-- Standard Version: 0.4 -->

VERSION      := $(shell cat VERSION 2>/dev/null || echo "0.0")
BUILD_NUMBER := $(shell git rev-list --count HEAD 2>/dev/null || echo "0")
GIT_SHA      := $(shell git rev-parse --short HEAD 2>/dev/null || echo "no-git")
BUILD_TS     := $(shell date +%H%M%S)
BUILD_ID     := v$(VERSION).b$(BUILD_NUMBER)-$(GIT_SHA)-$(BUILD_TS)

.PHONY: help fmt lint test build clean info install-e2e

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

info: ## Show build information
	@echo "Build ID: $(BUILD_ID)"

build-libs: ## Build shared libraries
	cd libraries/ui-core && npm install && npm run build

# Handle uv availability
UV := $(shell if command -v uv >/dev/null 2>&1; then echo uv; elif [ -f ~/.local/bin/uv ]; then echo ~/.local/bin/uv; else echo uv; fi)
RUN_UV := $(UV) run

fmt: fmt-web fmt-mobile ## Format all source code

fmt-web: ## Format web source code
	$(RUN_UV) ruff format src/backend
	cd src/frontend && npm run format

fmt-mobile: ## Format mobile source code
	cd src/mobile && npm run format

lint: lint-web lint-mobile ## Run all static analysis

lint-web: ## Run web static analysis
	PYTHONPATH=. $(RUN_UV) ruff check src/backend
	cd src/frontend && npm run lint

lint-mobile: ## Run mobile static analysis
	cd src/mobile && npm run lint

code-scan: ## Run source-level security scanners
	@echo "Running Source Code Security Scans..."
	cd src/frontend && npm audit
	uv run pip-audit
	uv run bandit -c pyproject.toml -r src/backend
	docker run --rm -v $(PWD):/src returntocorp/semgrep semgrep --config auto /src --error

container-scan: ## Run container vulnerability scanner
	@echo "Running Container Security Scan..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(HOME)/.cache:/root/.cache/ \
		aquasec/trivy image --exit-code 1 --ignore-unfixed PRODUCT_NAME:latest

test: test-web test-mobile ## Run all unit and integration tests

test-web: ## Run web unit and integration tests
	PYTHONPATH=. $(RUN_UV) pytest src/backend/tests/

test-mobile: ## Run mobile unit tests
	cd src/mobile && npm run test

install-e2e: ## Install E2E dependencies
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && nvm use --lts && npm install

test-mobile-e2e: ## Run Maestro mobile E2E tests
	export PATH="$$PATH:$$HOME/.maestro/bin" && maestro test src/mobile/.maestro/

test-mobile-e2e-ui: ## Run Maestro Studio for mobile E2E
	export PATH="$$PATH:$$HOME/.maestro/bin" && maestro studio

test-e2e: install-e2e ## Run Playwright E2E tests (Mocked)
	-pkill -f "uvicorn.*8001" || true
	-pkill -f "vite.*5174" || true
	rm -f e2e-test.db
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && nvm use --lts && AUTO_SEED_DATA=true MOCK_SES=true ENABLE_TEST_BACKDOOR=true npx playwright test

test-e2e-ui: ## Run Playwright E2E tests in UI mode
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && nvm use --lts && AUTO_SEED_DATA=true ENABLE_TEST_BACKDOOR=true npx playwright test --ui

test-e2e-system: install-e2e ## Run Playwright E2E tests against real backend
	-pkill -f "uvicorn.*8001" || true
	-pkill -f "vite.*5174" || true
	rm -f e2e-test.db
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && nvm use --lts && PLAYWRIGHT_MODE=SYSTEM AUTO_SEED_DATA=true ENABLE_TEST_BACKDOOR=true npx playwright test

test-server: ## Run servers specifically for E2E tests (Template)
	mkdir -p logs
	(PYTHONPATH=. DATABASE_URL=sqlite+aiosqlite:///./e2e-test.db AUTO_SEED_DATA=true TEST_MODE=true ENABLE_TEST_BACKDOOR=true uv run uvicorn src.backend.main:app --port 8001 > logs/e2e-backend.log 2>&1) & (cd src/frontend && VITE_API_URL=http://localhost:8001 npm run dev -- --port 5174 > ../../logs/e2e-frontend.log 2>&1)

dev: ## Run development servers
	(PYTHONPATH=. uv run uvicorn src.backend.main:app --reload --port 8000) & (cd src/frontend && npm run dev)

build: build-container build-mobile ## Build all components for production

build-container: ## Build the web frontend and docker container
	cd src/frontend && VITE_BUILD_ID=$(BUILD_ID) npm run build
	docker build --platform linux/amd64 --load --build-arg VITE_BUILD_ID=$(BUILD_ID) -t PRODUCT_NAME:latest -t PRODUCT_NAME:$(BUILD_ID) .

build-mobile: ## Build the mobile Android export
	cd src/mobile && npm run build:android

clean: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache src/frontend/dist src/frontend/node_modules
