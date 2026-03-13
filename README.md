# Sadhana-Vak — संस्कृत वाक्

**A real-time, fully-offline English → Sanskrit voice-to-voice AI system.**

Sadhana-Vak integrates a large language model (Qwen3-14B), a Pāṇinian formal grammar verifier (CLTK, Apache 2.0), and VITS/Piper Sanskrit TTS — all running locally on Apple Silicon with no internet dependency at runtime.

---

## Quick Start

### Prerequisites

| Requirement | Notes |
|---|---|
| macOS 14+ (Apple Silicon) | M2 Max 96GB recommended |
| Python 3.12 | Required for pre-built `aiortc` ARM64 wheels |
| Node.js 20+ | For the Next.js frontend |
| [Ollama](https://ollama.com) | Runs Qwen3-14B locally |
| Git LFS | For model files (optional) |

---

### 1 — Pull the LLM

```bash
ollama pull qwen3:14b
```

---

### 2 — Backend setup

```bash
cd backend

# Copy and edit environment variables
cp .env.example .env

# Create Python virtual environment (Python 3.12 required)
python3.12 -m venv .venv
source .venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# (Optional) Install platform-specific audio/ML deps:
#   pip install piper-tts          # TTS (requires espeak-ng: brew install espeak-ng)
#   pip install sherpa-onnx        # STT (Moonshine-Small)

# Seed the dictionary database (only needed once)
python scripts/build_dictionary_db.py

# Start the API server
uvicorn main:app --reload
# → API available at http://localhost:8000
# → Auto-docs at http://localhost:8000/docs
# → Health check at http://localhost:8000/health
```

---

### 3 — Frontend setup

```bash
cd frontend
npm install
npm run dev
# → UI available at http://localhost:3000
```

---

## Model Files

Place downloaded models in `backend/models/`:

| Model | File | Source |
|---|---|---|
| Moonshine-Small (STT) | `models/moonshine-small/` | [useful-transformers/moonshine](https://github.com/usefultransformers/moonshine) |
| Sanskrit VITS (TTS) | `models/vits-sanskrit.onnx` (+ `.json`) | Fine-tune via [Piper](https://github.com/rhasspy/piper) on IIT-Madras dataset |
| Silero VAD | `models/silero_vad.onnx` | [snakers4/silero-vad](https://github.com/snakers4/silero-vad) |

> **Note:** Qwen3-14B runs via Ollama — no GGUF file needed for the default setup.

---

## Features

| Feature | Status | Route |
|---|---|---|
| English → Sanskrit translation (voice + text) | ✅ | `/` |
| Pāṇinian grammar confidence scoring | ✅ | `/` |
| 3D vocal tract visualization | ⚙️ Phase III | `/` |
| Alphabet Explorer (50 phonemes, click-to-pronounce) | ✅ | `/alphabet` |
| Sanskrit Dictionary (93 MW entries, FTS5 search, declension tables) | ✅ | `/dictionary` |
| Subhāṣita Practice Panel (14 aphorisms, word chips, grammar analysis) | ✅ | `/practice` |
| IAST Verify Mode (live Devanāgarī preview, grammar check) | ✅ | `/verify` |

---

## Architecture Docs

| Doc | Description |
|---|---|
| [01-architectural-review.md](docs/architecture/01-architectural-review.md) | Critical risk review: GPLv3 traps, verifier scope, TTS gaps |
| [02-hardware-analysis.md](docs/architecture/02-hardware-analysis.md) | M2 Max memory bandwidth analysis |
| [03-machine-calibrated-roadmap.md](docs/architecture/03-machine-calibrated-roadmap.md) | Hardware-specific implementation roadmap |
| [04-nextjs-ux-protocol-analysis.md](docs/architecture/04-nextjs-ux-protocol-analysis.md) | WebRTC vs WebSocket, Silero VAD, 3D lip-sync |
| [05-srs.md](docs/architecture/05-srs.md) | Master Software Requirements Specification |
| [06-tech-stack.md](docs/architecture/06-tech-stack.md) | Approved technology stack with license matrix |
| [07-studio-shell.md](docs/architecture/07-studio-shell.md) | Sanskrit Studio Shell — pages, data, APIs |

---

## License

All production dependencies are **Apache 2.0, MIT, or BSD** licensed.
`sanskrit_parser` (GPLv3) is **not used** in this project. See [06-tech-stack.md](docs/architecture/06-tech-stack.md) for the full compatibility matrix.
