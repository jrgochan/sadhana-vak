#!/usr/bin/env python3
"""
test_pipeline.py — End-to-end pipeline test against the live FastAPI backend.

Tests the full chain:
    Text input → POST /translate → Devanāgarī + IAST + grammar score
    Sanskrit text → POST /speak → base64 WAV + phoneme timings
    Studio: GET /studio/lookup + GET /studio/declension

Usage:
    python backend/scripts/test_pipeline.py
    python backend/scripts/test_pipeline.py --url http://localhost:8000
    python backend/scripts/test_pipeline.py --text "Knowledge is power"
"""
import argparse
import base64
import json
import sys
import time
import urllib.request
import urllib.error

class C:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BLUE = "\033[0;34m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

def ok(label, val=""):   print(f"  {C.GREEN}✓{C.RESET} {label}" + (f"  {C.DIM}{val}{C.RESET}" if val else ""))
def warn(label, val=""): print(f"  {C.YELLOW}⚠{C.RESET} {label}" + (f"  {C.DIM}{val}{C.RESET}" if val else ""))
def fail(label, val=""): print(f"  {C.RED}✗{C.RESET} {label}" + (f"  {C.DIM}{val}{C.RESET}" if val else ""))
def section(msg):        print(f"\n{C.BOLD}{C.BLUE}▸ {msg}{C.RESET}")


def post_json(url: str, payload: dict, label: str) -> dict | None:
    data    = json.dumps(payload).encode()
    req     = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0      = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            elapsed = (time.perf_counter() - t0) * 1000
            result  = json.loads(resp.read().decode())
            return result, elapsed
    except urllib.error.HTTPError as e:
        fail(f"{label} → HTTP {e.code}: {e.read().decode()[:200]}")
        return None, 0
    except urllib.error.URLError as e:
        fail(f"{label} → Connection failed: {e.reason}")
        return None, 0


def get_json(url: str, label: str) -> dict | None:
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            elapsed = (time.perf_counter() - t0) * 1000
            return json.loads(resp.read().decode()), elapsed
    except urllib.error.HTTPError as e:
        fail(f"{label} → HTTP {e.code}")
        return None, 0
    except urllib.error.URLError as e:
        fail(f"{label} → {e.reason}")
        return None, 0


def test_translate(base_url: str, text: str) -> bool:
    section(f"Test 1 · Translation — \"{text}\"")
    result, ms = post_json(f"{base_url}/api/v1/translate", {"text": text, "register": "classical"}, "translate")
    if result is None:
        return False

    keys = {"translation", "iast", "word_analysis", "grammar_score"}
    missing = keys - set(result.keys())
    if missing:
        fail(f"Response missing keys: {missing}")
        return False

    translation = result.get("translation", "")
    iast        = result.get("iast", "")
    gs          = result.get("grammar_score", {})
    wa          = result.get("word_analysis", [])

    ok(f"Translation returned in {ms:.0f} ms")
    ok(f"Devanāgarī:  {translation}")
    ok(f"IAST:        {iast}")
    ok(f"Grammar:     {gs.get('status','')}  (score {gs.get('score',0):.2f})")
    ok(f"Word analysis: {len(wa)} words")

    if not translation:
        warn("Translation field is empty — LLM may not have returned Sanskrit text")
    if ms > 10_000:
        warn(f"Latency {ms:.0f}ms is above 10s — check Ollama model load time")

    return True


def test_speak(base_url: str, sanskrit_text: str) -> bool:
    section(f"Test 2 · TTS — \"{sanskrit_text}\"")
    result, ms = post_json(f"{base_url}/api/v1/speak", {"sanskrit_text": sanskrit_text}, "speak")
    if result is None:
        return False

    audio_b64 = result.get("audio_b64", "")
    phonemes  = result.get("phoneme_timings", [])

    if not audio_b64:
        fail("audio_b64 field is empty")
        return False

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as e:
        fail(f"Could not base64-decode audio: {e}")
        return False

    is_wav = audio_bytes[:4] == b"RIFF"
    ok(f"Speech generated in {ms:.0f} ms")
    ok(f"Audio: {len(audio_bytes):,} bytes  {'(valid WAV)' if is_wav else '(not WAV — check TTS service)'}")
    ok(f"Phoneme timings: {len(phonemes)} entries")

    if len(phonemes) == 0:
        warn("No phoneme timings — real-time 3D visualization won't sync (FR4)")

    return True


def test_studio(base_url: str) -> bool:
    section("Test 3 · Studio API Endpoints")
    all_ok = True

    # Dictionary lookup
    result, ms = get_json(f"{base_url}/api/v1/studio/lookup?q=dharma", "lookup")
    if result is not None:
        if isinstance(result, list) and len(result) > 0:
            ok(f"Lookup 'dharma' → {len(result)} result(s) in {ms:.0f}ms")
            ok(f"  First entry: {result[0].get('iast','')} — {result[0].get('definitions','')[:60]}…")
        elif isinstance(result, list):
            warn("Lookup returned 0 results — check dictionary seeding")
        else:
            fail("Unexpected lookup response shape")
            all_ok = False
    else:
        all_ok = False

    # Empty search
    result2, _ = get_json(f"{base_url}/api/v1/studio/lookup?q=xyzqwerty123", "lookup (no result)")
    if result2 is not None:
        if isinstance(result2, list) and len(result2) == 0:
            ok("Empty-result lookup returns []  (no crash)")
        else:
            warn(f"Expected [], got: {str(result2)[:80]}")

    # Declension
    result3, ms3 = get_json(f"{base_url}/api/v1/studio/declension?word=dharma", "declension")
    if result3 is not None and "forms" in result3:
        ok(f"Declension 'dharma' → {len(result3['forms'])} case rows in {ms3:.0f}ms")
    elif result3 is None:
        all_ok = False
    else:
        warn("Declension endpoint returned unexpected structure")

    # 404 for unknown word
    try:
        urllib.request.urlopen(f"{base_url}/api/v1/studio/declension?word=xyznotaword", timeout=5)
        warn("Expected 404 for unknown word, but got 200")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            ok("Unknown word returns 404  (correct)")
        else:
            warn(f"Unexpected HTTP {e.code} for unknown word")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Sadhana-Vak end-to-end pipeline test")
    parser.add_argument("--url",  default="http://localhost:8000")
    parser.add_argument("--text", default="Knowledge is the highest virtue")
    args = parser.parse_args()

    print(f"\n{C.BOLD}Sadhana-Vak — End-to-End Pipeline Test{C.RESET}")
    print("─" * 45)

    results = {
        "translate": test_translate(args.url, args.text),
        "speak":     test_speak(args.url, "अहं गच्छामि"),
        "studio":    test_studio(args.url),
    }

    section("Results")
    passed = sum(results.values())
    total  = len(results)
    for name, r in results.items():
        (ok if r else fail)(f"{name:12s} {'PASS' if r else 'FAIL'}")

    print()
    if passed == total:
        print(f"  {C.GREEN}{C.BOLD}{passed}/{total} tests passed ✓{C.RESET}\n")
        sys.exit(0)
    else:
        print(f"  {C.RED}{C.BOLD}{passed}/{total} tests passed{C.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
