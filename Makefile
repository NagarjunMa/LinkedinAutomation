.DEFAULT_GOAL := help
.PHONY: help install dev backend frontend test test-backend test-frontend lint build clean stop migrate seed shell-backend logs

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
BACKEND_PORT := 8000
FRONTEND_PORT := 3000
PYTHON       := python3.11

help: ## Show this help
	@echo "Prism Pro — make targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install backend + frontend dependencies
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt
	cd $(FRONTEND_DIR) && npm install

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
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ --ignore=tests/golden -v

test-frontend: ## Run frontend lint + type check + build
	cd $(FRONTEND_DIR) && npm run lint && npx tsc --noEmit && npm run build

lint: ## Lint backend (ruff) + frontend (next lint)
	cd $(BACKEND_DIR) && ruff check app/ --select=E,F --ignore=E501,E402 || true
	cd $(FRONTEND_DIR) && npm run lint

build: ## Build frontend production bundle
	cd $(FRONTEND_DIR) && npm run build

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
