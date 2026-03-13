"""
DictionaryService — queries the Monier-Williams SQLite FTS5 database
and looks up declension paradigms from the static JSON dataset.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH    = os.path.join(ROOT, "data", "monier_williams.db")
PARA_PATH  = os.path.join(ROOT, "data", "paradigms.json")


@dataclass
class DictEntry:
    word:       str
    iast:       str
    devanagari: str
    pos:        str
    stem_class: str
    definitions: str
    root:       str


@dataclass
class DeclensionForm:
    case:     str
    singular: str
    dual:     str
    plural:   str


@dataclass
class DeclensionResult:
    word:       str
    iast:       str
    stem_class: str
    gender:     str
    forms:      list[DeclensionForm]


class DictionaryService:
    _instance: "DictionaryService | None" = None

    def __init__(self) -> None:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(
                f"Dictionary DB not found at {DB_PATH}. "
                "Run: python backend/scripts/build_dictionary_db.py"
            )
        self._db_path = DB_PATH

        # Load paradigms JSON into memory once
        with open(PARA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        self._templates: dict = data["paradigm_templates"]
        self._word_map:  dict = data["word_map"]

    # ── Singleton accessor ────────────────────────────────────────────
    @classmethod
    def get(cls) -> "DictionaryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Dictionary lookup ─────────────────────────────────────────────
    def lookup(self, query: str, page: int = 1, per_page: int = 20) -> list[DictEntry]:
        """Full-text search over word, iast, devanagari, and definitions."""
        if not query or not query.strip():
            return []

        offset = (max(page, 1) - 1) * per_page
        q = query.strip()

        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # FTS5 search with PREFIX match so "gan" matches "gam", "gati" etc.
            try:
                cur.execute(
                    """
                    SELECT d.word, d.iast, d.devanagari, d.pos, d.class, d.definitions, d.root
                    FROM dictionary_fts fts
                    JOIN dictionary d ON d.id = fts.rowid
                    WHERE dictionary_fts MATCH ?
                    ORDER BY rank
                    LIMIT ? OFFSET ?
                    """,
                    (f"{q}*", per_page, offset),
                )
            except sqlite3.OperationalError:
                # Fallback: plain LIKE search if FTS query syntax fails
                like_q = f"%{q}%"
                cur.execute(
                    """
                    SELECT word, iast, devanagari, pos, class, definitions, root
                    FROM dictionary
                    WHERE word LIKE ? OR iast LIKE ? OR definitions LIKE ?
                    LIMIT ? OFFSET ?
                    """,
                    (like_q, like_q, like_q, per_page, offset),
                )

            rows = cur.fetchall()

        return [
            DictEntry(
                word=r["word"],
                iast=r["iast"],
                devanagari=r["devanagari"],
                pos=r["pos"] or "",
                stem_class=r["class"] or "",
                definitions=r["definitions"] or "",
                root=r["root"] or "",
            )
            for r in rows
        ]

    # ── Paradigm/Declension lookup ────────────────────────────────────
    def declension(self, word_key: str, stem_class: str = "", gender: str = "") -> DeclensionResult | None:
        """
        Return the declension table for a noun.
        word_key should match keys in the word_map (lowercase, no diacritics).
        If not found in the paradigm map, returns None.
        """
        mapping = self._word_map.get(word_key)
        if mapping is None:
            return None

        template_key, mapped_gender = mapping
        resolved_gender = gender or mapped_gender
        template = self._templates.get(template_key)
        if template is None:
            return None

        # Look up the base word for IAST display
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT iast FROM dictionary WHERE word = ? LIMIT 1", (word_key,))
            row = cur.fetchone()

        resolved_iast = row["iast"] if row else word_key

        forms = [
            DeclensionForm(
                case=c["case"],
                singular=c["singular"],
                dual=c["dual"],
                plural=c["plural"],
            )
            for c in template["cases"]
        ]

        return DeclensionResult(
            word=word_key,
            iast=resolved_iast,
            stem_class=template_key,
            gender=resolved_gender,
            forms=forms,
        )
