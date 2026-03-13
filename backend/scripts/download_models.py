#!/usr/bin/env python3
"""
download_models.py — Download AI model files required by Sadhana-Vak backend.

Usage:
    python backend/scripts/download_models.py           # download everything missing
    python backend/scripts/download_models.py --stt     # Moonshine-Small only
    python backend/scripts/download_models.py --vad     # Silero VAD only
    python backend/scripts/download_models.py --list    # show model status without downloading
    python backend/scripts/download_models.py --force   # re-download even if present

Models downloaded:
    • Moonshine-Small (STT)  — Apache 2.0  — ~80MB
    • Silero VAD v5          — MIT          — ~1MB

Models NOT downloaded here (manual steps required):
    • Qwen3-14B              — via Ollama: `ollama pull qwen3:14b`
    • Sanskrit VITS (TTS)    — fine-tune via Piper on IIT-Madras dataset
"""
import argparse
import sys
import urllib.request
import shutil
import tarfile
from pathlib import Path

class C:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def ok(msg):   print(f"{C.GREEN}  ✓{C.RESET} {msg}")
def warn(msg): print(f"{C.YELLOW}  ⚠{C.RESET} {msg}")
def err(msg):  print(f"{C.RED}  ✗{C.RESET} {msg}")
def step(msg): print(f"\n{C.BOLD}▸ {msg}{C.RESET}")

BACKEND_DIR = Path(__file__).parent.parent
MODELS_DIR  = BACKEND_DIR / "models"

# ── Model registry ────────────────────────────────────────────────────────────
MODELS = {
    "vad": {
        "name":    "Silero VAD v5",
        "license": "MIT",
        "size":    "~1 MB",
        "dest":    MODELS_DIR / "silero_vad.onnx",
        "url":     "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx",
        "type":    "single_file",
    },
    "stt": {
        "name":    "Moonshine-Base (Sherpa-ONNX)",
        "license": "Apache 2.0",
        "size":    "~150 MB",
        "dest":    MODELS_DIR / "moonshine-base",
        "url":     "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-moonshine-base-en-int8.tar.bz2",
        "type":    "tar_bz2",
        "strip":   1,  # strip one path component after extract
    },
}


def _progress_hook(dest_label: str):
    """urllib reporthook that prints a simple progress bar."""
    def hook(count, block_size, total_size):
        if total_size <= 0:
            return
        pct = min(100, int(count * block_size * 100 / total_size))
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r  [{bar}] {pct}% — {dest_label}", end="", flush=True)
        if pct >= 100:
            print()  # newline
    return hook


def download_model(key: str, force: bool = False) -> bool:
    """Download a single model by key. Returns True on success."""
    m = MODELS[key]
    dest: Path = m["dest"]
    url:  str  = m["url"]

    step(f"Downloading {m['name']} ({m['size']}, {m['license']})")

    if not force and dest.exists():
        ok(f"Already present: {dest.relative_to(BACKEND_DIR)}")
        return True

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MODELS_DIR / f"_tmp_{key}"

    try:
        print(f"  URL: {url}")
        urllib.request.urlretrieve(url, tmp, reporthook=_progress_hook(m["name"]))

        if m["type"] == "single_file":
            shutil.move(str(tmp), str(dest))
            ok(f"Saved to {dest.relative_to(BACKEND_DIR)}")

        elif m["type"] == "tar_bz2":
            dest.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tmp, "r:bz2") as tf:
                strip = m.get("strip", 0)
                for member in tf.getmembers():
                    parts = Path(member.name).parts
                    # Strip first N path components
                    if len(parts) <= strip:
                        continue
                    member.name = str(Path(*parts[strip:]))
                    tf.extract(member, dest)
            tmp.unlink(missing_ok=True)
            ok(f"Extracted to {dest.relative_to(BACKEND_DIR)}/")

        return True

    except Exception as exc:
        err(f"Download failed: {exc}")
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return False


def list_models():
    """Print the status of every registered model."""
    print(f"\n{C.BOLD}Model Status{C.RESET}\n")
    for key, m in MODELS.items():
        dest = m["dest"]
        status = f"{C.GREEN}present{C.RESET}" if dest.exists() else f"{C.YELLOW}missing{C.RESET}"
        print(f"  [{key:6s}] {m['name']:40s} {status}  ({m['size']}, {m['license']})")
        print(f"           Path: {dest.relative_to(BACKEND_DIR)}")
    print()
    print(f"  [llm   ] Qwen3-14B via Ollama — run: {C.BOLD}ollama pull qwen3:14b{C.RESET}")
    print("  [tts   ] Sanskrit VITS — fine-tune via Piper on IIT-Madras dataset")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Download Sadhana-Vak AI model files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--stt",   action="store_true", help="Download Moonshine-Small (STT)")
    parser.add_argument("--vad",   action="store_true", help="Download Silero VAD")
    parser.add_argument("--list",  action="store_true", help="List model status without downloading")
    parser.add_argument("--force", action="store_true", help="Re-download even if already present")
    args = parser.parse_args()

    print(f"\n{C.BOLD}Sadhana-Vak — Model Downloader{C.RESET}")
    print("─" * 46)

    if args.list:
        list_models()
        return

    # Determine which models to download
    if args.stt or args.vad:
        targets = []
        if args.stt:
            targets.append("stt")
        if args.vad:
            targets.append("vad")
    else:
        # Download all missing models
        targets = list(MODELS.keys())

    results = {}
    for key in targets:
        results[key] = download_model(key, force=args.force)

    print()
    ok_count = sum(v for v in results.values())
    if ok_count == len(results):
        print(f"{C.GREEN}{C.BOLD}All models ready.{C.RESET}")
    else:
        warn(f"{ok_count}/{len(results)} models downloaded successfully.")
        sys.exit(1)


if __name__ == "__main__":
    main()
