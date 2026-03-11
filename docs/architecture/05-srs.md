# Sadhana-Vak: Software Requirements Specification (SRS)

**Version:** 1.0 — Calibrated for Apple M2 Max (96GB), macOS 26.2  
**Date:** 2026-03-11

---

## 1. Introduction

Sadhana-Vak is a 100%-offline, real-time voice-to-voice translation assistant that converts spoken English to grammatically correct, phonetically accurate Sanskrit using Paninian formal grammar as a validation oracle. All inference runs locally on consumer Apple Silicon hardware, with no recurring API costs and no network dependency.

---

## 2. Functional Requirements

| ID | Requirement |
|---|---|
| **FR1** | The system shall translate spoken English into Classical Sanskrit text and speech, end-to-end, with no internet connection required at runtime. |
| **FR2** | The system shall score every generated Sanskrit output against a Paninian morphological grammar engine and surface a confidence band (`VALID / PROBABLE / ERROR`) to the user before audio playback. |
| **FR3** | The system shall display generated Sanskrit simultaneously in Devanāgarī script and IAST romanization. |
| **FR4** | The system shall display articulatory feedback (vocal tract visualization) synchronized to the TTS phoneme stream. |
| **FR5** | The system shall detect voice activity in the browser before transmitting audio to the backend (no streaming of silence). |
| **FR6** | The system shall accept a user-selectable register: **Classical Sanskrit** (default) or **Vedic Sanskrit** (Phase III). |

---

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| **NFR1** | End-to-end latency (speech in → audio out) | **≤ 500ms** on M2 Max hardware |
| **NFR2** | Recurring operational cost | **$0.00** (fully local) |
| **NFR3** | User data persistence | All audio/text data remains local; session wipe removes all ephemeral state |
| **NFR4** | Minimum RAM | 16 GB system RAM (optimal: 32 GB+) |
| **NFR5** | Model storage footprint | ~20–30 GB on disk (multiple model variants) |
| **NFR6** | Primary platform | macOS 13+ (Next.js browser UI + Python FastAPI backend) |
| **NFR7** | License compliance | All production dependencies must be Apache 2.0, MIT, or BSD licensed. No GPLv3 in distributed code. |

---

## 4. System Architecture

```
Browser (localhost:3000)
  └── Next.js 15 App
        ├── [WASM] Silero VAD ← only opens stream when speech detected
        ├── [WebRTC] Audio stream → FastAPI /offer
        ├── [SSE] Translation results ← FastAPI /translate
        └── [REST] Audio playback ← FastAPI /speak

Python FastAPI (localhost:8000)
  ├── /offer      → aiortc WebRTC endpoint → PCM → STT
  ├── /translate  → LLM → Verifier → returns JSON { translation, word_analysis, grammar_score }
  ├── /speak      → VITS TTS → returns { audio_bytes, phoneme_timings }
  └── /health     → Checks all models loaded
```

---

## 5. Pipeline Data Model

The LLM must return structured JSON. This is enforced via system prompt + llama.cpp grammar sampling:

```json
{
  "input_english": "I am going to the forest",
  "translation": "अहं वनं गच्छामि",
  "iast": "ahaṃ vanaṃ gacchāmi",
  "register": "classical",
  "word_analysis": [
    {"pada": "अहम्", "root": "अस्मद्", "case": "nominative", "number": "singular", "purusa": "1st"},
    {"pada": "वनम्", "root": "वन", "case": "accusative", "number": "singular", "gender": "neuter"},
    {"pada": "गच्छामि", "root": "गम्", "lakara": "laṭ", "purusa": "1st", "number": "singular"}
  ],
  "grammar_score": {
    "score": 0.97,
    "status": "VALID",
    "notes": "Derivation path confirmed."
  }
}
```

---

## 6. Phased Delivery Roadmap

| Phase | Goal | Target Duration |
|---|---|---|
| **0** | Foundation: license matrix, corpus setup, DCS test set, VAD/STT sanity | 1 week |
| **I** | Python FastAPI pipeline: STT + Qwen3-14B + grammar scorer + VITS TTS | 3 weeks |
| **II** | Next.js frontend: mic capture, Devanāgarī display, confidence band UI | 3 weeks |
| **III** | Real-time 3D vocal visualization (React Three Fiber / VocalTractLab) | 3 weeks |
| **IV** | Vedic register + Sanskrit voice input (IndicASR) | Ongoing |
| **V** | Mobile port: iOS/Android via ExecuTorch, smaller model tier | 6 weeks |

---

## 7. Risk Register

| Severity | Risk | Mitigation |
|---|---|---|
| 🔴 | GPLv3 in dependency chain | Use CLTK/SanskritShala (Apache 2.0) instead of `sanskrit_parser` for distribution |
| 🔴 | LLM hallucinating ungrammatical Sanskrit | Structured JSON output + Paninian scorer; few-shot DCS examples in prompt |
| 🟡 | Sanskrit TTS sounding like Hindi | Fine-tune VITS on IIT-Madras Sanskrit corpus; budget an overnight training run |
| 🟡 | WebRTC peer connection issues over localhost | Test with `aiortc` echo server before full pipeline; fallback to WebSocket for dev |
| 🟢 | Latency budget under pressure | M2 Max hardware gives ~4x headroom vs. target; speculative decoding not needed |
