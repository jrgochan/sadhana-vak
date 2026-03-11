# Sadhana-Vak
**A Real-Time Offline Sanskrit Voice-to-Voice System**

Sadhana-Vak is an edge-native experimental application that integrates contemporary Large Language Models with Paninian Formal Logic. It is designed to run 100% offline, targeting Apple Silicon hardware, to provide real-time English-to-Sanskrit speech translation, grammatical validation, and audio sythesis.

## Architecture Documentation

A comprehensive multi-pass architectural review was conducted during the planning phase. The full specifications and hardware-calibrated roadmap are maintained locally in the `docs/` directory:

- [docs/architecture/sadhana_vak_machine_calibration.md](docs/architecture/sadhana_vak_machine_calibration.md) - The master implementation roadmap, calibrated specifically for M2 Max 96GB hardware.
- [docs/architecture/sadhana_vak_nextjs_ux_analysis.md](docs/architecture/sadhana_vak_nextjs_ux_analysis.md) - Deep dive into WebRTC audio streaming, in-browser VAD (WebAssembly), and 3D lip-sync synchronization.
- [docs/architecture/sadhana_vak_hardware_analysis.md](docs/architecture/sadhana_vak_hardware_analysis.md) - Analysis of memory bandwidth constraints, ExecuTorch vs MLC-LLM runtimes, and GPU scaling.
- [docs/architecture/sadhana_vak_review.md](docs/architecture/sadhana_vak_review.md) - Initial linguistic review covering GPLv3 licensing traps, Paninian verifier heuristics, and Sanskrit STT/TTS models.

## Repository Structure

The project is split into a monorepo architecture for rapid prototyping:

- `frontend/`: A Next.js 15 (React) application rendering the UI, capturing mic audio, running Silero VAD strictly in the browser via WebAssembly, and streaming audio bytes to the backend via WebRTC.
- `backend/`: A Python FastAPI environment acting as the AI orchestrator. Wraps Sherpa-ONNX (STT), Qwen3-14B (LLM), CLTK/sanskrit-parser (Grammar Verifier), and Piper/VITS (TTS).
- `docs/`: Centralized research and architectural blueprints.

## Setup Instructions (Phase I & II)

### 1. Backend (Python API)
The backend requires `python3.12` to install pre-compiled ARM64 wheel binaries for the `aiortc` library, sidestepping FFmpeg 8 Homebrew compilation issues.

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Frontend (Next.js UX)
```bash
cd frontend
npm install
npm run dev
```
