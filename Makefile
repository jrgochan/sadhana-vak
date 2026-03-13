# =============================================================================
# Sadhana-Vak — Developer Makefile
# संस्कृत वाक् — Offline Sanskrit AI System
#
# Usage:
#   make setup      — First-time environment bootstrap
#   make dev        — Start backend + frontend simultaneously
#   make backend    — Start only the FastAPI backend
#   make frontend   — Start only the Next.js frontend
#   make health     — Check all services are running
#   make test       — Run end-to-end pipeline tests
#   make bench      — Run latency benchmark vs. NFR1 budget
#   make verify     — Launch interactive Sanskrit grammar REPL
#   make models     — Show model download status
#   make seed       — (Re)seed the dictionary database
#   make lint       — Lint Python backend code
#   make clean      — Remove generated files (DB, __pycache__)
# =============================================================================

SHELL := /bin/bash
PYTHON := $(shell command -v python3.12 2>/dev/null || command -v python3)
VENV   := backend/.venv
BIN    := $(VENV)/bin

# Colors for echo
BOLD  := \033[1m
GREEN := \033[0;32m
BLUE  := \033[0;34m
RESET := \033[0m

.PHONY: all setup dev backend frontend health test bench verify models seed lint clean help

# Default: show help
all: help

# ── help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@printf "$(BOLD)Sadhana-Vak — Developer Makefile$(RESET)\n"
	@printf "$(BOLD)संस्कृत वाक् — Offline Sanskrit AI System$(RESET)\n\n"
	@printf "$(BLUE)Usage:$(RESET) make <target>\n\n"
	@printf "$(BOLD)First-time setup$(RESET)\n"
	@printf "  $(GREEN)make setup$(RESET)     — Bootstrap Python venv, install deps, seed DB, check Ollama\n"
	@printf "  $(GREEN)make models$(RESET)    — Show & download missing model files\n\n"
	@printf "$(BOLD)Development$(RESET)\n"
	@printf "  $(GREEN)make dev$(RESET)       — Start backend + frontend together\n"
	@printf "  $(GREEN)make backend$(RESET)   — Start FastAPI backend only (port 8000)\n"
	@printf "  $(GREEN)make frontend$(RESET)  — Start Next.js frontend only (port 3000)\n\n"
	@printf "$(BOLD)Testing & Verification$(RESET)\n"
	@printf "  $(GREEN)make health$(RESET)    — Check all services are alive\n"
	@printf "  $(GREEN)make test$(RESET)      — Run end-to-end pipeline tests\n"
	@printf "  $(GREEN)make bench$(RESET)     — Benchmark latency vs. NFR1 (≤500ms)\n"
	@printf "  $(GREEN)make verify$(RESET)    — Interactive Sanskrit grammar REPL\n\n"
	@printf "$(BOLD)Data$(RESET)\n"
	@printf "  $(GREEN)make seed$(RESET)      — (Re)seed the Monier-Williams dictionary DB\n\n"
	@printf "$(BOLD)Code Quality$(RESET)\n"
	@printf "  $(GREEN)make lint$(RESET)      — Lint Python code with ruff\n"
	@printf "  $(GREEN)make clean$(RESET)     — Remove generated __pycache__, logs, etc.\n\n"

# ── setup ─────────────────────────────────────────────────────────────────────
setup:
	@bash backend/scripts/setup.sh

# ── dev (both backend + frontend) ────────────────────────────────────────────
dev: $(VENV)
	@printf "\n$(BOLD)Starting Sadhana-Vak development servers...$(RESET)\n\n"
	@printf "  Backend:  $(GREEN)http://localhost:8000$(RESET)\n"
	@printf "  Frontend: $(GREEN)http://localhost:3000$(RESET)\n\n"
	@# Run both concurrently; Ctrl-C kills both
	@trap 'kill 0' EXIT; \
	  ( cd backend && source .venv/bin/activate && uvicorn main:app --reload ) & \
	  ( cd frontend && npm run dev ) & \
	  wait

# ── backend only ──────────────────────────────────────────────────────────────
backend: $(VENV)
	@printf "$(BOLD)Starting FastAPI backend$(RESET)  → http://localhost:8000\n"
	@printf "Docs at http://localhost:8000/docs\n\n"
	@cd backend && source .venv/bin/activate && uvicorn main:app --reload

# ── frontend only ─────────────────────────────────────────────────────────────
frontend:
	@printf "$(BOLD)Starting Next.js frontend$(RESET)  → http://localhost:3000\n\n"
	@cd frontend && npm run dev

# ── health check ──────────────────────────────────────────────────────────────
health: $(VENV)
	@cd backend && source .venv/bin/activate && python scripts/check_health.py

# ── e2e tests ─────────────────────────────────────────────────────────────────
test: $(VENV)
	@printf "$(BOLD)Running end-to-end pipeline tests$(RESET)\n"
	@cd backend && source .venv/bin/activate && python scripts/test_pipeline.py

# ── benchmark ────────────────────────────────────────────────────────────────
bench: $(VENV)
	@printf "$(BOLD)Running latency benchmark (NFR1: ≤500ms)$(RESET)\n"
	@cd backend && source .venv/bin/activate && python scripts/benchmark_pipeline.py

# ── interactive verifier ──────────────────────────────────────────────────────
verify: $(VENV)
	@cd backend && source .venv/bin/activate && python scripts/verify_sanskrit.py

# ── model management ──────────────────────────────────────────────────────────
models: $(VENV)
	@cd backend && source .venv/bin/activate && python scripts/download_models.py --list

models-download: $(VENV)
	@cd backend && source .venv/bin/activate && python scripts/download_models.py

# ── seed dictionary DB ────────────────────────────────────────────────────────
seed: $(VENV)
	@printf "$(BOLD)Seeding Monier-Williams dictionary database$(RESET)\n"
	@cd backend && source .venv/bin/activate && python scripts/build_dictionary_db.py

# ── STT self-test ─────────────────────────────────────────────────────────────
test-stt: $(VENV)
	@cd backend && source .venv/bin/activate && python scripts/test_stt.py

# ── CLTK self-test ────────────────────────────────────────────────────────────
test-cltk: $(VENV)
	@cd backend && source .venv/bin/activate && python scripts/test_cltk.py

# ── linting ──────────────────────────────────────────────────────────────────
lint: $(VENV)
	@cd backend && source .venv/bin/activate && \
	  (command -v ruff &>/dev/null && ruff check . || \
	   (pip install ruff --quiet && ruff check .))
	@cd frontend && npm run lint

# ── clean ─────────────────────────────────────────────────────────────────────
clean:
	@printf "$(BOLD)Cleaning generated files$(RESET)\n"
	@find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find backend -name "*.pyc" -delete 2>/dev/null || true
	@find frontend -name ".next" -type d -exec rm -rf {} + 2>/dev/null || true
	@printf "  Done.\n"

# ── venv guard ────────────────────────────────────────────────────────────────
$(VENV):
	@printf "$(BOLD)Creating Python virtual environment$(RESET)\n"
	@$(PYTHON) -m venv $(VENV)
	@$(BIN)/pip install --upgrade pip --quiet
	@$(BIN)/pip install -r backend/requirements.txt --quiet
	@printf "  Done. Activate with: source backend/.venv/bin/activate\n"
