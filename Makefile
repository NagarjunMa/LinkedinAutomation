.DEFAULT_GOAL := help
.PHONY: help install setup verify verify-ci verify-backend-ci verify-frontend-ci dev backend frontend test test-backend test-frontend test-frontend-unit test-frontend-e2e test-agents test-golden test-smoke lint lint-backend lint-frontend typecheck build audit audit-backend audit-frontend clean stop migrate shell-backend logs

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
BACKEND_PORT := 8000
FRONTEND_PORT := 3000
PYTHON       := python3.11
BACKEND_TEST_ENV := OPENAI_API_KEY=test SUPABASE_URL=https://test.supabase.co SUPABASE_ANON_KEY=test SUPABASE_SERVICE_ROLE_KEY=test DATABASE_URL=sqlite:///:memory:
FRONTEND_BUILD_ENV := NEXT_PUBLIC_API_URL=https://api.example.com NEXT_PUBLIC_SUPABASE_URL=https://test.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=test
FRONTEND_E2E_ENV := PRISM_PRO_PUBLIC_PREVIEW_ONLY=false NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_SUPABASE_URL=https://test.supabase.co NEXT_PUBLIC_SUPABASE_ANON_KEY=test

help: ## Show this help
	@echo "Prism Pro — make targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install backend + frontend dependencies
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt
	cd $(FRONTEND_DIR) && npm install

setup: install ## Zero-to-running: install deps + install Playwright Chromium
	cd $(BACKEND_DIR) && $(PYTHON) -m playwright install --with-deps chromium
	@echo ""
	@echo "Setup complete. Next:"
	@echo "  make verify     - sanity-check agents without LLM (no API key needed)"
	@echo "  make dev        - boot backend + frontend"

verify: test-smoke test-agents ## One-shot sanity check (no LLM, no API keys required)
	@echo ""
	@echo "All agent paths verified against mocked OpenAI + real fixtures."
	@echo "To exercise the real LLM, run:  make test-golden"

verify-ci: verify-backend-ci verify-frontend-ci ## Run both local CI suites except Docker/Postgres/secret-scan services

verify-backend-ci: lint-backend test-backend audit-backend ## Run backend lint, coverage tests, and dependency audit

verify-frontend-ci: verify-contracts lint-frontend typecheck build test-frontend audit-frontend ## Run contracts, frontend lint, types, build, tests, and audit

.PHONY: contracts-generate contracts-check verify-contracts

contracts-generate: ## Regenerate declared FastAPI/OpenAPI and TypeScript transport contracts offline
	cd $(FRONTEND_DIR) && PYTHON=$(PYTHON) npm run contracts:generate

contracts-check: ## Fail on missing or stale generated contracts without rewriting them
	cd $(FRONTEND_DIR) && PYTHON=$(PYTHON) npm run contracts:check

verify-contracts: ## Test contract tooling and verify committed artifacts (requires Python + Node)
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check scripts/export_openapi.py tests/scripts/test_export_openapi.py --select=E,F --ignore=E501
	cd $(FRONTEND_DIR) && npx eslint scripts/api-contracts.mjs scripts/api-contracts.test.mjs --max-warnings=0
	cd $(FRONTEND_DIR) && npm run test:contracts
	$(MAKE) contracts-check

dev: ## Run backend + frontend together (Ctrl+C stops both)
	@echo "→ backend  http://localhost:$(BACKEND_PORT)"
	@echo "→ frontend http://localhost:$(FRONTEND_PORT)"
	@trap 'kill 0' INT TERM EXIT; \
		(cd $(BACKEND_DIR)  && $(PYTHON) -m uvicorn app.main:app --reload --port $(BACKEND_PORT)) & \
		(cd $(FRONTEND_DIR) && npm run dev) & \
		wait

backend: ## Run backend only
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload --port $(BACKEND_PORT)

frontend: ## Run frontend only
	cd $(FRONTEND_DIR) && npm run dev

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend pytest (ignores golden snapshots)
	cd $(BACKEND_DIR) && $(BACKEND_TEST_ENV) $(PYTHON) -m pytest tests/ --ignore=tests/golden -v --maxfail=5 --cov-fail-under=80

test-agents: ## Run only agent service tests (evaluator, rewriter, extractor, tailor, hallucination_guard) - no LLM
	cd $(BACKEND_DIR) && $(BACKEND_TEST_ENV) $(PYTHON) -m pytest tests/services/resume tests/services/jd -v -o addopts=""

test-smoke: ## Boot the FastAPI app + assert routes register (no DB, no LLM)
	cd $(BACKEND_DIR) && $(BACKEND_TEST_ENV) $(PYTHON) -m pytest tests/test_smoke.py -v -o addopts=""

test-golden: ## Run golden snapshots against REAL OpenAI (requires OPENAI_API_KEY) - costs about $0.05
	@if [ -z "$$OPENAI_API_KEY" ]; then echo "OPENAI_API_KEY not set — skipping"; exit 1; fi
	cd $(BACKEND_DIR) && RUN_GOLDEN=1 $(PYTHON) -m pytest tests/golden -v

test-frontend: test-frontend-unit test-frontend-e2e ## Run frontend unit coverage and MVP Playwright smoke

test-frontend-unit: ## Run frontend unit tests with coverage
	cd $(FRONTEND_DIR) && npm run test:coverage

test-frontend-e2e: ## Run the MVP Playwright smoke suite
	cd $(FRONTEND_DIR) && $(FRONTEND_E2E_ENV) npm run test:e2e

lint: lint-backend lint-frontend ## Lint backend (ruff) + frontend

lint-backend: ## Lint backend with ruff
	cd $(BACKEND_DIR) && $(PYTHON) -m ruff check app/ --select=E,F --ignore=E501,E402

lint-frontend: ## Lint frontend with ESLint
	cd $(FRONTEND_DIR) && npm run lint

typecheck: ## Type-check frontend
	cd $(FRONTEND_DIR) && npx tsc --noEmit

build: ## Build frontend production bundle
	cd $(FRONTEND_DIR) && $(FRONTEND_BUILD_ENV) npm run build

audit: audit-backend audit-frontend ## Run backend + frontend dependency audits

audit-backend: ## Run backend dependency audit
	cd $(BACKEND_DIR) && $(PYTHON) -m pip_audit -r requirements.lock

audit-frontend: ## Run frontend production dependency audit
	cd $(FRONTEND_DIR) && npm audit --omit=dev --audit-level=high

clean: ## Wipe build artifacts + caches
	rm -rf $(FRONTEND_DIR)/.next $(FRONTEND_DIR)/node_modules/.cache
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

stop: ## Kill processes on dev ports
	-lsof -ti:$(BACKEND_PORT) | xargs kill -9 2>/dev/null || true
	-lsof -ti:$(FRONTEND_PORT) | xargs kill -9 2>/dev/null || true
	@echo "stopped processes on ports $(BACKEND_PORT) and $(FRONTEND_PORT)"

migrate: ## Apply Alembic migrations to current DB
	cd $(BACKEND_DIR) && alembic upgrade head

shell-backend: ## Open backend Python REPL with app + db loaded
	cd $(BACKEND_DIR) && $(PYTHON) -c "from app.main import app; from app.db.session import SessionLocal; db = SessionLocal(); print('app, db ready')" -i

logs: ## Tail backend log files
	tail -f $(BACKEND_DIR)/logs/*.log
