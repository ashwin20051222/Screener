# ScreenerDesk - one-command control. All paths are repo-relative; nothing leaves your machine
# except the documented daily/weekly fetches of official exchange/AMFI files (see DATA_SOURCES.md).
PY       ?= python3.12
VENV     := .venv
PIP      := $(VENV)/bin/pip
PYTHON   := $(VENV)/bin/python

.DEFAULT_GOAL := help
.PHONY: help venv install sync-daily sync-weekly synkinbox status coverage run web-build test clean

help: ## show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

$(VENV):
	$(PY) -m venv $(VENV)

venv: $(VENV) ## create the local python 3.12 virtualenv

install: venv ## install dependencies into .venv
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt
	@echo "deps ready: $(VENV)"

sync-daily: ## daily EOD sync: walk back for published bhavcopies (NSE CM+FO, BSE CM) + corp actions
	$(PYTHON) scripts/sync_daily.py

sync-weekly: ## weekly: inbox imports first, then equity/ETF masters, F&O lots, index lists, AMFI, FBIL
	$(PYTHON) scripts/sync_weekly.py

synkinbox: ## process only the manual-import drop zone (data/inbox/)
	$(PYTHON) scripts/sync_inbox.py

status: ## print db photo: per-source as-of dates, security counts, recent jobs
	$(PYTHON) scripts/db_info.py

coverage: ## measure per-filter DB coverage (all rows + NIFTY100) and write docs/DATA_COVERAGE.md
	$(PYTHON) scripts/coverage.py

run: ## start the app at http://127.0.0.1:8787 (serves React UI + FastAPI API; host/port from config/settings.yaml)
	$(PYTHON) -m app.main

web-build: ## build the production React UI served by `make run`
	cd apps/web && npm run build

test: ## run the offline test suite (fixtures only, never the network)
	$(PYTHON) -m pytest -q

clean: ## remove caches only; never touches data/raw (your traceable raw files)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
