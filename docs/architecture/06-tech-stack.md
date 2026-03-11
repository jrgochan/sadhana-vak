# Sadhana-Vak: Approved Technology Stack

**Last updated:** 2026-03-11

This document is the canonical list of every library used in production. Any new dependency must be added here with its license noted before merging.

---

## Frontend (`frontend/`)

| Layer | Library | Version | License | Notes |
|---|---|---|---|---|
| Framework | **Next.js** | 15.x | MIT | App Router; local-first mode (no SSR needed) |
| Language | **TypeScript** | 5.x | Apache 2.0 | Strict mode enabled |
| Styling | **Tailwind CSS** | 4.x | MIT | v4 config via `@tailwind` |
| Fonts | **Noto Sans Devanagari** | (Google Fonts CDN or local) | OFL 1.1 | Full Sanskrit Unicode coverage |
| In-browser AI | **onnxruntime-web** | 1.17+ | MIT | Runs Silero VAD model in WASM |
| VAD Model | **Silero VAD** | v5 | MIT | 1MB ONNX; <1ms per 32ms chunk |
| 3D Visuals | **React Three Fiber** | 8.x | MIT | Phase III; mounts Three.js into React |
| Audio | **Web Audio API + MediaRecorder** | (native browser) | — | No library needed |
| WebRTC | **native browser RTCPeerConnection** | — | — | Connects to aiortc on backend |

---

## Backend (`backend/`)

| Layer | Library | Version | License | Notes |
|---|---|---|---|---|
| Web Framework | **FastAPI** | 0.110+ | MIT | Async; auto OpenAPI docs at `/docs` |
| ASGI Server | **uvicorn** | 0.29+ | BSD | `--reload` for dev |
| WebRTC | **aiortc** | 1.8+ | BSD | Python WebRTC peer; uses `av` for audio decode |
| LLM Runtime | **llama-cpp-python** | 0.2.62+ | MIT | Runs GGUF on Metal GPU (`n_gpu_layers=-1`) |
| STT | **sherpa-onnx** | latest | Apache 2.0 | Wraps Moonshine-Small or Whisper |
| TTS | **piper-tts** | latest | MIT | VITS architecture; outputs wav + phoneme timings |
| Grammar | **CLTK** | 1.x | MIT | Sanskrit morphological analysis (Apache 2.0 fallback) |
| Transliteration | **indic-transliteration** | 2.3+ | MIT | IAST ↔ Devanāgarī normalization |
| Config | **pydantic-settings** | 2.x | MIT | Env-var overrides for model paths |

---

## AI Models (stored in `backend/models/`)

| Model | File | Size | License | Source |
|---|---|---|---|---|
| **Qwen3-14B-Instruct Q4_K_M** | `qwen3-14b-instruct.Q4_K_M.gguf` | ~8 GB | Apache 2.0 | [Hugging Face: Qwen/Qwen3-14B](https://huggingface.co/Qwen/Qwen3-14B) |
| **Moonshine-Small** | `moonshine-small/` | ~80 MB | Apache 2.0 | [useful-transformers/moonshine](https://github.com/usefultransformers/moonshine) |
| **Silero VAD** | `silero_vad.onnx` | ~1 MB | MIT | [snakers4/silero-vad](https://github.com/snakers4/silero-vad) |
| **VITS Sanskrit** | `vits-sanskrit.onnx` | ~300 MB | MIT (after fine-tune) | Fine-tuned via Piper on IIT-Madras dataset |

---

## License Compatibility Matrix

All production dependencies must be **Apache 2.0, MIT, or BSD** licensed. The following are **explicitly excluded** from distribution:

| Library | License | Status | Notes |
|---|---|---|---|
| `sanskrit_parser` | **GPLv3** | ❌ Excluded from distribution | May be used in local dev tooling only |
| Sanskrit Heritage Engine | **AGPL** | ❌ Excluded from distribution | Research reference only |
| VocalTractLab (C++ core) | **GPL** | ❌ Excluded from distribution | Use Python API for pre-rendering offline only |
