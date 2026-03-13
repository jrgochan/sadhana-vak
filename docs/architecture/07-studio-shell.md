# Sadhana-Vak: Sanskrit Studio Shell

**Phase V addition** — six interactive Sanskrit study pages built on top of the existing voice-to-voice pipeline.

> This document supersedes the original Phase V "Mobile Port" entry in `05-srs.md`.

## Architecture

The Studio Shell lives entirely in the frontend (`frontend/src/app/`) as a Next.js App Router sub-application. All pages share the Studio sidebar layout and call the FastAPI backend for data.

## Pages

| Route | Component | Description |
|---|---|---|
| `/alphabet` | `app/alphabet/page.tsx` | Phoneme explorer — 50 Sanskrit characters in tabbed grids by articulation class. Click-to-pronounce via TTS cache. |
| `/dictionary` | `app/dictionary/page.tsx` | Debounced full-text search over 93 Monier-Williams entries (SQLite FTS5). Lazy-loaded declension tables. |
| `/practice` | `app/practice/page.tsx` | 14 Subhāṣita aphorisms in an animated carousel. Per-word chips with grammar notes + live dictionary lookup. |
| `/verify` | `app/verify/page.tsx` | IAST text input with live Devanāgarī preview (via `@indic-transliteration/sanscript`). Grammar analysis via Pāṇinian Verifier API. |

## Backend API Additions

| Endpoint | File | Description |
|---|---|---|
| `GET /api/v1/studio/lookup` | `api/routes_studio.py` | FTS5 word lookup in `monier_williams.db` |
| `GET /api/v1/studio/declension` | `api/routes_studio.py` | Paradigm table lookup from `paradigms.json` |

## Data Files

| File | Contents |
|---|---|
| `backend/data/monier_williams.db` | SQLite FTS5 database (~93 seed entries from Monier-Williams) |
| `backend/data/paradigms.json` | 31 noun/verb declension paradigm tables |
| `frontend/src/data/subhasitas.ts` | 14 curated Subhāṣita entries with word-by-word annotations |

## Dependencies Added

| Package | Location | License |
|---|---|---|
| `framer-motion` | frontend | MIT |
| `lucide-react` | frontend | ISC |
| `@indic-transliteration/sanscript` | frontend | MIT |
