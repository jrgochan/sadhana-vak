#!/usr/bin/env bash
# =============================================================================
# setup.sh — One-command developer environment bootstrap for Sadhana-Vak
#
# Usage:
#   ./backend/scripts/setup.sh
#
# What it does:
#   1. Verifies Python 3.12+ is available
#   2. Creates backend/.venv if it doesn't exist
#   3. Installs pip dependencies from requirements.txt
#   4. Verifies / installs platform-specific packages (piper-tts, sherpa-onnx)
#   5. Seeds the Monier-Williams dictionary database
#   6. Checks that Ollama is running and Qwen3-14B is pulled
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$BACKEND_DIR/.." && pwd)"
VENV_DIR="$BACKEND_DIR/.venv"

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}  ✓${RESET} $*"; }
warn() { echo -e "${YELLOW}  ⚠${RESET} $*"; }
err()  { echo -e "${RED}  ✗${RESET} $*"; }
step() { echo -e "\n${BOLD}${BLUE}▸ $*${RESET}"; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════╗"
echo "║   Sadhana-Vak — Developer Environment Setup     ║"
echo "║   संस्कृत वाक् — Offline Sanskrit AI System     ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Step 1: Python version check ─────────────────────────────────────────────
step "Checking Python version"
PYTHON=$(command -v python3.12 2>/dev/null || command -v python3 2>/dev/null || true)
if [ -z "$PYTHON" ]; then
  err "Python 3.12+ not found. Install from https://python.org"
  exit 1
fi

PY_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]; }; then
  warn "Python $PY_VERSION found, but 3.12+ is strongly recommended (aiortc ARM64 wheels)"
else
  ok "Python $PY_VERSION found at $PYTHON"
fi

# ── Step 2: Create virtual environment ───────────────────────────────────────
step "Setting up Python virtual environment"
if [ -d "$VENV_DIR" ]; then
  ok "Virtual environment already exists at .venv/"
else
  $PYTHON -m venv "$VENV_DIR"
  ok "Created .venv/ with $PYTHON"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet

# ── Step 3: Install core dependencies ────────────────────────────────────────
step "Installing core Python dependencies"
pip install -r "$BACKEND_DIR/requirements.txt" --quiet
ok "Core dependencies installed"

# ── Step 4: Platform-specific ML packages ────────────────────────────────────
step "Checking platform-specific ML packages"

# sherpa-onnx (STT)
if python -c "import sherpa_onnx" 2>/dev/null; then
  ok "sherpa-onnx already installed"
else
  warn "sherpa-onnx not installed — installing (Apache 2.0, 64MB)"
  pip install sherpa-onnx --quiet && ok "sherpa-onnx installed" || warn "sherpa-onnx install failed — STT will run in stub mode"
fi

# piper-tts (requires espeak-ng system library)
if python -c "import piper" 2>/dev/null; then
  ok "piper-tts already installed"
elif command -v espeak-ng &>/dev/null; then
  warn "piper-tts not installed — installing (MIT)"
  pip install piper-tts --quiet && ok "piper-tts installed" || warn "piper-tts install failed — TTS will run in stub mode"
else
  warn "espeak-ng not found (required by piper-tts). Install with: brew install espeak-ng"
  warn "TTS will run in silent stub mode until espeak-ng + piper-tts are installed"
fi

# cltk (grammar verifier)
if python -c "import cltk" 2>/dev/null; then
  ok "cltk already installed"
else
  warn "cltk not installed — installing (Apache 2.0)"
  pip install cltk --quiet && ok "cltk installed" || warn "cltk install failed — verifier will use heuristic stub"
fi

# ── Step 5: Copy .env if needed ──────────────────────────────────────────────
step "Checking environment configuration"
if [ -f "$BACKEND_DIR/.env" ]; then
  ok ".env file found"
else
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  ok "Created .env from .env.example — review model paths before starting"
fi

# ── Step 6: Seed dictionary database ─────────────────────────────────────────
step "Seeding Monier-Williams dictionary database"
DB_PATH="$BACKEND_DIR/data/monier_williams.db"
if [ -f "$DB_PATH" ]; then
  ok "Dictionary database already exists"
else
  cd "$BACKEND_DIR" && python scripts/build_dictionary_db.py
  ok "Dictionary database created"
fi

# ── Step 7: Check Ollama + model ─────────────────────────────────────────────
step "Checking Ollama (LLM backend)"
OLLAMA_MODEL=${OLLAMA_MODEL:-"qwen3:14b"}
if ! command -v ollama &>/dev/null; then
  warn "Ollama not found. Install from https://ollama.com then run: ollama pull $OLLAMA_MODEL"
elif ! curl -sf "http://localhost:11434/api/tags" | grep -q "$OLLAMA_MODEL" 2>/dev/null; then
  warn "Ollama is installed but '$OLLAMA_MODEL' not pulled yet. Run: ollama pull $OLLAMA_MODEL"
else
  ok "Ollama is running with $OLLAMA_MODEL"
fi

# ── Step 8: Check model files ─────────────────────────────────────────────────
step "Checking AI model files in backend/models/"
MODELS_DIR="$BACKEND_DIR/models"
[ -d "$MODELS_DIR" ] || mkdir -p "$MODELS_DIR"

check_model() {
  local label=$1; local path=$2; local hint=$3
  if [ -e "$path" ]; then ok "$label found"; else warn "$label not found — $hint"; fi
}
check_model "Moonshine-Small (STT)" "$MODELS_DIR/moonshine-small" \
  "Run: python backend/scripts/download_models.py --stt"
check_model "Silero VAD"             "$MODELS_DIR/silero_vad.onnx" \
  "Run: python backend/scripts/download_models.py --vad"
check_model "Sanskrit VITS (TTS)"    "$MODELS_DIR/vits-sanskrit.onnx" \
  "Fine-tune via Piper on IIT-Madras dataset — see docs/architecture/06-tech-stack.md"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}Setup complete!${RESET}"
echo ""
echo -e "  Start the backend:  ${BOLD}source backend/.venv/bin/activate && uvicorn main:app --reload${RESET}"
echo -e "  Start the frontend: ${BOLD}cd frontend && npm install && npm run dev${RESET}"
echo -e "  Or use:             ${BOLD}make dev${RESET}"
echo ""
