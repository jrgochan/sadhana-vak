import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# IMPORTANT: sanskrit_parser (GPLv3) is BANNED from this codebase.
# We use CLTK (Apache 2.0) as the morphological analysis backend.
# See docs/architecture/06-tech-stack.md § License Compatibility Matrix.
# ---------------------------------------------------------------------------

class VerifierService:
    """
    Paninian grammar confidence scorer using CLTK's Sanskrit morphological
    analyzer (Apache 2.0 license) as the analysis backend.

    The verifier is a SCORER, not a hard gate. It returns:
      - VALID    (score ≥ 0.75): Clear derivation path found
      - PROBABLE (score 0.40–0.74): Partial / ambiguous analysis
      - ERROR    (score < 0.40): No valid morphological analysis found

    See 01-architectural-review.md §1 for the rationale.
    """

    def __init__(self):
        self._cltk_available = False
        self._analyzer = None
        self._load_analyzer()

    def _load_analyzer(self):
        try:
            # CLTK's NLP pipeline for Sanskrit
            from cltk import NLP
            self._nlp = NLP(language="sans")  # "sans" = Sanskrit ISO 639-3
            self._cltk_available = True
            logger.info("VerifierService: CLTK Sanskrit NLP pipeline loaded (Apache 2.0).")
        except ImportError:
            logger.warning(
                "VerifierService: cltk not installed. "
                "Install with: pip install cltk  (Apache 2.0). "
                "Using heuristic stub fallback."
            )
            self._cltk_available = False
        except Exception as e:
            logger.warning(f"VerifierService: CLTK load failed ({e}). Using stub fallback.")
            self._cltk_available = False

    def score_grammar(self, sanskrit_text: str) -> dict:
        """
        Score a Sanskrit string for Pāṇinian morphological validity.
        Returns { score: float, status: str, notes: str }.
        """
        if not sanskrit_text or not sanskrit_text.strip():
            return {
                "score": 0.0,
                "status": "ERROR",
                "notes": "Empty input — nothing to analyze.",
            }

        if self._cltk_available:
            return self._score_with_cltk(sanskrit_text)
        else:
            return self._heuristic_score(sanskrit_text)

    def _score_with_cltk(self, text: str) -> dict:
        """Run CLTK NLP pipeline and score based on successful token analysis."""
        try:
            doc = self._nlp.analyze(text=text)

            # Count tokens that received morphological annotation
            total   = len(doc.words)
            scored  = sum(1 for w in doc.words if w.upos and w.upos != "X")
            coverage = scored / total if total > 0 else 0.0

            # Build human-readable analysis notes
            notes_parts = []
            for w in doc.words[:8]:  # cap at 8 to avoid wall-of-text
                if w.upos and w.upos != "X":
                    tags = []
                    if w.features:
                        tags = [f"{k}={v}" for k, v in list(w.features.items())[:3]]
                    notes_parts.append(
                        f"{w.string}: {w.upos}" + (f" [{', '.join(tags)}]" if tags else "")
                    )

            notes = "; ".join(notes_parts) if notes_parts else "Morphological analysis complete."

            if coverage >= 0.75:
                return {"score": round(0.75 + 0.25 * coverage, 3), "status": "VALID",    "notes": notes}
            elif coverage >= 0.40:
                return {"score": round(coverage, 3),               "status": "PROBABLE", "notes": notes}
            else:
                return {
                    "score": round(coverage, 3),
                    "status": "ERROR",
                    "notes": f"Low morphological coverage ({scored}/{total} tokens recognized). {notes}",
                }

        except Exception as e:
            logger.error(f"CLTK analysis error: {e}")
            return {
                "score": 0.0,
                "status": "ERROR",
                "notes": f"CLTK analysis failed: {str(e)}",
            }

    def _heuristic_score(self, text: str) -> dict:
        """
        Lightweight heuristic fallback when CLTK is not installed.
        Checks for Devanāgarī script content and basic structure.
        """

        # Count Devanāgarī characters (Unicode block 0900–097F)
        dev_chars = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
        total_alpha = sum(1 for ch in text if ch.isalpha() or "\u0900" <= ch <= "\u097f")

        if total_alpha == 0:
            return {"score": 0.0, "status": "ERROR", "notes": "No recognizable text found."}

        coverage = dev_chars / total_alpha if total_alpha > 0 else 0.0

        if coverage >= 0.8:
            return {
                "score": 0.60,
                "status": "PROBABLE",
                "notes": "Heuristic: Devanāgarī script detected. Install `cltk` for full Pāṇinian analysis.",
            }
        else:
            return {
                "score": 0.35,
                "status": "PROBABLE",
                "notes": "Heuristic: Mixed or IAST input. Install `cltk` for full Pāṇinian analysis.",
            }
