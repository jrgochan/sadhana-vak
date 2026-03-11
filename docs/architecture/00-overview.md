# Sadhana-Vak: Documentation Index

This directory contains the full architecture specification for the Sadhana-Vak real-time Sanskrit voice-to-voice system. The documents reflect an end-to-end design review process conducted prior to implementation.

## Documents

| Doc | Description |
|---|---|
| [01-architectural-review.md](01-architectural-review.md) | Initial deep-dive identifying critical risks: GPLv3 licensing, Paninian verifier scope, TTS/STT Sanskrit gaps, prompt engineering strategy |
| [02-hardware-analysis.md](02-hardware-analysis.md) | Analysis of memory bandwidth limits, Unity overhead, ExecuTorch vs MLC-LLM runtime conflict |
| [03-machine-calibrated-roadmap.md](03-machine-calibrated-roadmap.md) | Hardware-specific plan update for the Apple M2 Max (96GB) dev machine. Supersedes generic targets. |
| [04-nextjs-ux-protocol-analysis.md](04-nextjs-ux-protocol-analysis.md) | Web frontend analysis: WebRTC vs WebSocket latency, in-browser VAD via WASM, 3D lip-sync sync protocol |
| [05-srs.md](05-srs.md) | **Master Software Requirements Specification** — the canonical set of functional and non-functional requirements |
| [06-tech-stack.md](06-tech-stack.md) | Final approved technology stack with version pins, licenses, and rationale |

## Key Decisions

1. **Primary language:** English → Sanskrit (Sanskrit voice input is Phase III scope)
2. **UI:** Next.js 15 (localhost:3000) + Python FastAPI (localhost:8000) monorepo
3. **Audio:** WebRTC (UDP) for mic → backend, not WebSockets (TCP)
4. **VAD:** Silero VAD running in browser via `onnxruntime-web` (WASM) — never streams silence to backend
5. **LLM:** Qwen3-14B Q4_K_M GGUF via llama.cpp, structured JSON output
6. **Grammar:** Paninian verifier as a *confidence scorer*, not a hard gate
7. **TTS:** VITS/Piper fine-tuned on Sanskrit corpus; returns `[audio_bytes, phoneme_timings]` for 3D sync
