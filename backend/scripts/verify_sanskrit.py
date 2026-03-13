#!/usr/bin/env python3
"""
verify_sanskrit.py — Interactive CLI for Pāṇinian grammar analysis.

Runs the CLTK-backed VerifierService on Sanskrit text entered by the user.
Useful for quickly checking whether a generated translation is grammatically sound.

Usage:
    python backend/scripts/verify_sanskrit.py
    python backend/scripts/verify_sanskrit.py "अहं गच्छामि"
    python backend/scripts/verify_sanskrit.py --file sentences.txt
    python backend/scripts/verify_sanskrit.py --iast "ahaṃ gacchāmi"

Options:
    --iast TEXT     Convert IAST input to Devanāgarī before analysis
    --file PATH     Analyze each line of a file
    --json          Output results as JSON (useful for piping to other tools)
    --detail        Show full morphological feature table
"""
import argparse
import json
import sys
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

STATUS_STYLE = {
    "VALID":    (C.GREEN,  "✓ VALID    — Pāṇinian derivation path confirmed"),
    "PROBABLE": (C.YELLOW, "〜 PROBABLE — Partial morphological analysis"),
    "ERROR":    (C.RED,    "✗ ERROR    — No valid derivation path found"),
}


def to_devanagari(iast_text: str) -> str:
    """Convert IAST to Devanāgarī using indic-transliteration."""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        return transliterate(iast_text, sanscript.IAST, sanscript.DEVANAGARI)
    except ImportError:
        print(f"  {C.YELLOW}⚠{C.RESET}  indic-transliteration not installed.")
        print(f"      Install: {C.DIM}pip install indic-transliteration{C.RESET}")
        return iast_text


def analyze(text: str, verifier, detail: bool) -> dict:
    """Run the verifier and return a result dict."""
    result = verifier.score_grammar(text)
    return result


def print_result(text: str, result: dict, detail: bool, verifier):
    status  = result.get("status", "ERROR")
    score   = result.get("score", 0.0)
    notes   = result.get("notes", "")
    color, label = STATUS_STYLE.get(status, (C.DIM, status))

    print()
    print(f"  {C.BOLD}Text:{C.RESET}   {text}")
    print(f"  Status:  {color}{label}{C.RESET}")
    score_bar_fill = int(score * 20)
    score_bar = "█" * score_bar_fill + "░" * (20 - score_bar_fill)
    print(f"  Score:   {color}{score_bar}{C.RESET}  {score:.0%}")

    if notes:
        print(f"\n  {C.DIM}Notes:{C.RESET}")
        # Pretty-print semicolon-separated notes
        note_parts = [n.strip() for n in notes.split(";") if n.strip()]
        if len(note_parts) > 1:
            for n in note_parts:
                print(f"    • {n}")
        else:
            print(f"    {notes}")

    if detail and verifier and verifier._cltk_available:
        # Re-run and show raw word table
        try:
            doc = verifier._nlp.analyze(text=text)
            if doc.words:
                print(f"\n  {C.DIM}{'Word':18s} {'UPOS':10s} {'Features'}{C.RESET}")
                print(f"  {'─'*18} {'─'*10} {'─'*40}")
                for w in doc.words:
                    feats = " ".join(f"{k}={v}" for k, v in (w.features or {}).items()) or "—"
                    print(f"  {w.string:18s} {(w.upos or '—'):10s} {C.DIM}{feats}{C.RESET}")
        except Exception as e:
            print(f"  {C.DIM}(Could not get word table: {e}){C.RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Sadhana-Vak Sanskrit grammar verifier CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("text", nargs="?", default=None,
                        help="Sanskrit text to analyze (Devanāgarī or IAST with --iast)")
    parser.add_argument("--iast",    metavar="TEXT", help="Convert from IAST before analyzing")
    parser.add_argument("--file",    metavar="PATH", help="Analyze each line of a file")
    parser.add_argument("--json",    action="store_true", help="Output as JSON")
    parser.add_argument("--detail",  action="store_true", help="Show full morphological feature table")
    args = parser.parse_args()

    print(f"\n{C.BOLD}Sadhana-Vak — Sanskrit Grammar Verifier{C.RESET}")
    print(f"{C.DIM}Powered by CLTK Sanskrit NLP pipeline (Apache 2.0){C.RESET}")
    print("─" * 45)

    # Load verifier
    try:
        from services.verifier import VerifierService
        verifier = VerifierService()
    except Exception as e:
        print(f"{C.RED}✗{C.RESET} Could not load VerifierService: {e}")
        sys.exit(1)

    backend = "CLTK Sanskrit NLP" if verifier._cltk_available else "heuristic stub"
    backend_color = C.GREEN if verifier._cltk_available else C.YELLOW
    print(f"  Backend: {backend_color}{backend}{C.RESET}\n")

    # Determine inputs
    texts = []
    if args.iast:
        texts.append(to_devanagari(args.iast))
    elif args.text:
        texts.append(args.text)
    elif args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"  {C.RED}✗{C.RESET}  File not found: {args.file}")
            sys.exit(1)
        texts = [line.strip() for line in p.read_text().splitlines() if line.strip()]
    else:
        # Interactive REPL
        print(f"  {C.DIM}Enter Sanskrit text (Devanāgarī) to analyze. Type 'quit' to exit.{C.RESET}\n")
        while True:
            try:
                text = input(f"  {C.BOLD}Sanskrit ▸{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  नमस्ते! 🙏")
                break
            if text.lower() in ("quit", "exit", "q"):
                print("  नमस्ते! 🙏")
                break
            if not text:
                continue
            # Allow IAST prefix shorthand: "iast: ahaṃ gacchāmi"
            if text.lower().startswith("iast:"):
                text = to_devanagari(text[5:].strip())
            result = analyze(text, verifier, args.detail)
            if args.json:
                print(json.dumps({"text": text, **result}, ensure_ascii=False, indent=2))
            else:
                print_result(text, result, args.detail, verifier)
        return

    # Batch mode
    all_results = []
    for text in texts:
        result = analyze(text, verifier, args.detail)
        all_results.append({"text": text, **result})
        if not args.json:
            print_result(text, result, args.detail, verifier)

    if args.json:
        print(json.dumps(all_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
