#!/usr/bin/env python3
"""
benchmark_pipeline.py — Measure latency of each pipeline stage vs. the SRS NFR1 budget.

SRS NFR1: End-to-end latency ≤ 500ms on M2 Max hardware.

Stages measured:
    1. Verifier (CLTK grammar scoring)  — target: ≤ 80ms
    2. TTS synthesis (Piper)            — target: ≤ 150ms
    3. Full translate endpoint          — target: ≤ 12,000ms (LLM dominates)
    4. Full speak endpoint              — measures TTS HTTP round-trip

Usage:
    python backend/scripts/benchmark_pipeline.py
    python backend/scripts/benchmark_pipeline.py --reps 5
    python backend/scripts/benchmark_pipeline.py --text "I seek knowledge"
"""
import argparse
import asyncio
import json
import statistics
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class C:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BLUE = "\033[0;34m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def bar(ms, target, label, width=24):
    pct  = min(1.0, ms / (target * 2.5))
    fill = int(pct * width)
    color = C.GREEN if ms <= target else C.YELLOW if ms <= target * 2 else C.RED
    b = "█" * fill + "░" * (width - fill)
    tgt_label = f"target ≤{target:.0f}ms"
    return f"  {label:26s}  {color}{b}{C.RESET}  {color}{ms:7.1f}ms{C.RESET}  {C.DIM}({tgt_label}){C.RESET}"


def section(msg): print(f"\n{C.BOLD}{C.BLUE}▸ {msg}{C.RESET}")


async def bench_verifier(reps: int):
    """Benchmark the CLTK verifier service directly."""
    section("Benchmark 1 · Verifier (CLTK morphological analysis)")
    try:
        from services.verifier import VerifierService
        svc = VerifierService()
    except Exception as e:
        print(f"  {C.RED}✗{C.RESET} Could not load VerifierService: {e}")
        return None

    # Use a mix of short and long sentences
    test_cases = [
        "अहं गच्छामि",
        "विद्या ददाति विनयम्",
        "सत्यं ब्रूयात् प्रियं ब्रूयात् न ब्रूयात् सत्यम् अप्रियम्",
        "धर्मो रक्षति रक्षितः",
    ]

    times = []
    for text in test_cases:
        t0 = time.perf_counter()
        for _ in range(reps):
            svc.score_grammar(text)
        elapsed = (time.perf_counter() - t0) / reps * 1000
        times.append(elapsed)
        backend = "cltk" if svc._cltk_available else "heuristic-stub"
        print(f"  {text[:40]:42s}  {C.DIM}{elapsed:5.1f}ms  [{backend}]{C.RESET}")

    if times:
        avg = statistics.mean(times)
        print()
        print(bar(avg, 80, "Verifier avg"))
        return avg
    return None


async def bench_tts(reps: int):
    """Benchmark the TTS service directly."""
    section("Benchmark 2 · TTS (Piper synthesis)")
    try:
        from services.tts import TTSService
        svc = TTSService()
    except Exception as e:
        print(f"  {C.RED}✗{C.RESET} Could not load TTSService: {e}")
        return None

    mode = "Piper (real)" if svc.voice else "stub (silence)"
    texts = [
        "अहं",
        "सत्यं ब्रूयात्",
        "विद्या ददाति विनयं विनयाद् याति पात्रताम्",
    ]

    times = []
    for text in texts:
        t0 = time.perf_counter()
        for _ in range(reps):
            await svc.generate_speech(text)
        elapsed = (time.perf_counter() - t0) / reps * 1000
        times.append(elapsed)
        print(f"  \"{text[:35]:37s}\"  {C.DIM}{elapsed:7.1f}ms{C.RESET}")

    if times:
        avg = statistics.mean(times)
        print()
        print(bar(avg, 150, f"TTS avg [{mode}]"))
        if not svc.voice:
            print(f"  {C.YELLOW}⚠{C.RESET}  {C.DIM}TTS running in stub mode — install piper-tts for real timings{C.RESET}")
        return avg
    return None


def bench_http_endpoint(url: str, method: str, payload: dict | None, label: str, target_ms: int, reps: int):
    """Benchmark an HTTP endpoint."""
    section(f"Benchmark · {label}")
    times = []
    for i in range(reps):
        t0 = time.perf_counter()
        try:
            data = json.dumps(payload).encode() if payload else None
            req  = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json"} if payload else {},
            )
            with urllib.request.urlopen(req, timeout=300):
                pass
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            print(f"  Run {i+1}/{reps}: {elapsed:7.1f} ms")
        except Exception as e:
            print(f"  {C.RED}✗{C.RESET}  Run {i+1}/{reps}: {e}")

    if not times:
        print(f"  {C.RED}✗{C.RESET}  All {reps} runs failed")
        return None

    avg = statistics.mean(times)
    p50 = statistics.median(times)
    p_max = max(times)
    print()
    print(bar(avg, target_ms, f"{label} avg"))
    print(f"  {C.DIM}p50={p50:.0f}ms  max={p_max:.0f}ms{C.RESET}")
    return avg


def main():
    parser = argparse.ArgumentParser(description="Sadhana-Vak pipeline benchmark")
    parser.add_argument("--url",  default="http://localhost:8000")
    parser.add_argument("--reps", type=int, default=3, help="Repetitions per benchmark")
    parser.add_argument("--text", default="Truth is the highest virtue", help="English text to translate")
    parser.add_argument("--local-only", action="store_true", help="Skip HTTP endpoint benchmarks")
    args = parser.parse_args()

    print(f"\n{C.BOLD}Sadhana-Vak — Pipeline Latency Benchmark{C.RESET}")
    print("SRS NFR1: end-to-end ≤ 500ms on M2 Max")
    print("─" * 60)

    loop = asyncio.get_event_loop()

    results = {}
    results["verifier"] = loop.run_until_complete(bench_verifier(args.reps))
    results["tts"]      = loop.run_until_complete(bench_tts(args.reps))

    if not args.local_only:
        results["/translate"] = bench_http_endpoint(
            f"{args.url}/api/v1/translate", "POST",
            {"text": args.text, "register": "classical"},
            "/translate endpoint", target_ms=15_000, reps=args.reps,
        )
        results["/speak"] = bench_http_endpoint(
            f"{args.url}/api/v1/speak", "POST",
            {"sanskrit_text": "अहं गच्छामि"},
            "/speak endpoint", target_ms=500, reps=args.reps,
        )

    # NFR1 summary
    section("NFR1 Latency Budget Summary")
    NFR1_BUDGET = {
        "verifier":   80,
        "tts":        150,
        "/translate": 15_000,
        "/speak":     500,
    }
    for key, ms in results.items():
        if ms is None:
            print(f"  {C.YELLOW}⚠{C.RESET}  {key:20s}  skipped / failed")
            continue
        target = NFR1_BUDGET.get(key, 500)
        status = (f"{C.GREEN}✓ PASS{C.RESET}" if ms <= target
                  else f"{C.YELLOW}⚠ SLOW{C.RESET}" if ms <= target * 2
                  else f"{C.RED}✗ OVER BUDGET{C.RESET}")
        print(f"  {status}  {key:20s}  {ms:7.1f}ms  (target ≤{target}ms)")

    print()


if __name__ == "__main__":
    main()
