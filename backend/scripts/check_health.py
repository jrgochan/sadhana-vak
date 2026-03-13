#!/usr/bin/env python3
"""
check_health.py — Verify every Sadhana-Vak service is alive before running the app.

Usage:
    python backend/scripts/check_health.py
    python backend/scripts/check_health.py --url http://localhost:8000

Checks:
    • FastAPI backend /health endpoint
    • Individual model load status (LLM, STT, TTS, Verifier)
    • Ollama reachability + model availability
    • Model files on disk
    • Frontend reachability (optional)
    • Dictionary database exists
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ── Colors ────────────────────────────────────────────────────────────────────
class C:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def ok(msg):   print(f"  {C.GREEN}✓{C.RESET} {msg}")
def warn(msg): print(f"  {C.YELLOW}⚠{C.RESET} {msg}")
def fail(msg): print(f"  {C.RED}✗{C.RESET} {msg}")
def section(msg): print(f"\n{C.BOLD}{msg}{C.RESET}")
def dim(msg):  print(f"  {C.DIM}{msg}{C.RESET}")

BACKEND_DIR = Path(__file__).parent.parent
MODELS_DIR  = BACKEND_DIR / "models"
DATA_DIR    = BACKEND_DIR / "data"


def check_url(url: str, label: str, timeout: int = 3) -> dict | None:
    """GET a URL and return parsed JSON, or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return data
    except urllib.error.URLError as e:
        fail(f"{label} — connection refused ({e.reason})")
        return None
    except Exception as e:
        fail(f"{label} — {e}")
        return None


def check_backend(base_url: str) -> bool:
    """Check the FastAPI /health endpoint."""
    section("1 · FastAPI Backend")
    data = check_url(f"{base_url}/health", "FastAPI backend")
    if data is None:
        dim("Start backend: uvicorn main:app --reload  (from backend/)")
        return False

    status = data.get("status", "unknown")
    all_ok = data.get("all_ok", False)
    if all_ok:
        ok(f"Backend healthy: {status}")
    else:
        warn(f"Backend degraded: {status}")

    models = data.get("models", {})
    for svc, info in models.items():
        loaded = info.get("loaded", False)
        if loaded:
            ok(f"  {svc:12s} loaded")
        else:
            backend_info = info.get("backend", info.get("path", info.get("model", "")))
            warn(f"  {svc:12s} NOT loaded  [{backend_info}]")
    return True


def check_ollama(base_url: str = "http://localhost:11434", model: str = "qwen3:14b") -> bool:
    """Check Ollama is running and the model is available."""
    section("2 · Ollama (LLM)")
    data = check_url(f"{base_url}/api/tags", "Ollama", timeout=2)
    if data is None:
        dim("Install Ollama: https://ollama.com  then: ollama serve")
        return False

    models = [m.get("name", "") for m in data.get("models", [])]
    # Check for exact or prefix match
    match = any(m == model or m.startswith(model.split(":")[0]) for m in models)
    if match:
        ok(f"Model '{model}' available in Ollama")
        return True
    else:
        warn(f"Model '{model}' NOT found in Ollama. Available: {models}")
        dim(f"Pull it: ollama pull {model}")
        return False


def check_model_files() -> int:
    """Check which model files exist on disk. Returns count of missing."""
    section("3 · Model Files")

    items = [
        ("Moonshine-Small (STT)",  MODELS_DIR / "moonshine-small", "sherpa-onnx dir",
         "python backend/scripts/download_models.py --stt"),
        ("Silero VAD",             MODELS_DIR / "silero_vad.onnx", "onnx file",
         "python backend/scripts/download_models.py --vad"),
        ("Sanskrit VITS (TTS)",    MODELS_DIR / "vits-sanskrit.onnx", "onnx file",
         "Fine-tune via Piper on IIT-Madras — see docs/architecture/06-tech-stack.md"),
    ]

    missing = 0
    for label, path, ftype, hint in items:
        if path.exists():
            size_mb = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6 if path.is_dir() \
                      else path.stat().st_size / 1e6
            ok(f"{label}  ({size_mb:.1f} MB)")
        else:
            warn(f"{label}  MISSING [{ftype}]")
            dim(f"Hint: {hint}")
            missing += 1
    return missing


def check_database() -> bool:
    """Check dictionary database exists."""
    section("4 · Dictionary Database")
    db = DATA_DIR / "monier_williams.db"
    paradigms = DATA_DIR / "paradigms.json"
    ok_flag = True
    if db.exists():
        size = db.stat().st_size / 1e3
        ok(f"monier_williams.db  ({size:.0f} KB)")
    else:
        warn("monier_williams.db not found")
        dim("Seed it: python backend/scripts/build_dictionary_db.py")
        ok_flag = False
    if paradigms.exists():
        ok("paradigms.json found")
    else:
        warn("paradigms.json not found — declension tables unavailable")
        ok_flag = False
    return ok_flag


def check_frontend(url: str = "http://localhost:3000") -> None:
    """Check whether the Next.js frontend is up (best-effort)."""
    section("5 · Frontend (Next.js)")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2):
            ok(f"Frontend reachable at {url}")
    except Exception:
        warn(f"Frontend not running at {url}")
        dim("Start it: cd frontend && npm run dev")


def main():
    parser = argparse.ArgumentParser(description="Sadhana-Vak health check")
    parser.add_argument("--url",     default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--ollama",  default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--model",   default=os.getenv("OLLAMA_MODEL", "qwen3:14b"))
    parser.add_argument("--no-frontend", action="store_true", help="Skip frontend check")
    args = parser.parse_args()

    print(f"\n{C.BOLD}Sadhana-Vak — System Health Check{C.RESET}")
    print("─" * 45)

    backend_ok = check_backend(args.url)
    ollama_ok  = check_ollama(args.ollama, args.model)
    missing    = check_model_files()
    db_ok      = check_database()
    if not args.no_frontend:
        check_frontend()

    # Summary
    section("Summary")
    issues = []
    if not backend_ok:
        issues.append("Backend not running")
    if not ollama_ok:
        issues.append(f"Ollama/{args.model} not available")
    if missing > 0:
        issues.append(f"{missing} model file(s) missing")
    if not db_ok:
        issues.append("Dictionary DB missing")

    if not issues:
        print(f"\n  {C.GREEN}{C.BOLD}All systems go! 🚀{C.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n  {C.YELLOW}{C.BOLD}{len(issues)} issue(s) to resolve:{C.RESET}")
        for iss in issues:
            print(f"    {C.YELLOW}•{C.RESET} {iss}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
