"""
Studio API routes — dictionary lookup and paradigm/declension endpoints.
Registered at prefix /api/v1/studio in main.py.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.dictionary import DictionaryService

router = APIRouter(prefix="/studio", tags=["studio"])


# ── Response models ───────────────────────────────────────────────────
class DictEntryOut(BaseModel):
    word:        str
    iast:        str
    devanagari:  str
    pos:         str
    stem_class:  str
    definitions: str
    root:        str


class DeclensionFormOut(BaseModel):
    case:     str
    singular: str
    dual:     str
    plural:   str


class DeclensionOut(BaseModel):
    word:       str
    iast:       str
    stem_class: str
    gender:     str
    forms:      list[DeclensionFormOut]


# ── Endpoints ─────────────────────────────────────────────────────────
@router.get("/lookup", response_model=list[DictEntryOut])
async def lookup_word(
    q:    str = Query(..., min_length=1, description="Search term (IAST, Devanāgarī, or English)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
):
    """Full-text search the Monier-Williams dictionary."""
    try:
        svc     = DictionaryService.get()
        results = svc.lookup(q, page=page)
        return [
            DictEntryOut(
                word=e.word,
                iast=e.iast,
                devanagari=e.devanagari,
                pos=e.pos,
                stem_class=e.stem_class,
                definitions=e.definitions,
                root=e.root,
            )
            for e in results
        ]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/declension", response_model=DeclensionOut)
async def get_declension(
    word:       str           = Query(..., description="Word key (lowercase, no diacritics)"),
    stem_class: Optional[str] = Query(None, description="Stem class override"),
    gender:     Optional[str] = Query(None, description="Gender override"),
):
    """
    Return the 8-case × 3-number declension table for a noun.
    Returns 404 if the word is not in the static paradigm dataset.
    """
    try:
        svc    = DictionaryService.get()
        result = svc.declension(word, stem_class or "", gender or "")
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Paradigm for '{word}' not yet catalogued."
            )
        return DeclensionOut(
            word=result.word,
            iast=result.iast,
            stem_class=result.stem_class,
            gender=result.gender,
            forms=[
                DeclensionFormOut(
                    case=f.case,
                    singular=f.singular,
                    dual=f.dual,
                    plural=f.plural,
                )
                for f in result.forms
            ],
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
