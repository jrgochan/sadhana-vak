# Sadhana-Vak: Machine-Calibrated Plan Update

**Target Development Machine (scanned 2026-03-11)**

| Component | Spec |
|---|---|
| Chip | **Apple M2 Max** |
| CPU Cores | 12 (8 performance + 4 efficiency) |
| GPU Cores | **38-core** integrated GPU |
| Unified Memory | **96 GB LPDDR5** |
| Memory Bandwidth | **~400 GB/s** (M2 Max spec) |
| Storage | **8 TB** Apple NVMe SSD (5.32 TB free) |
| Display | Liquid Retina XDR 3456×2234 |
| OS | macOS 26.2 (Tahoe) |

This machine is **not a constraint — it is a supercomputer for this task.** Almost every limitation cited in the prior three architectural reviews disappears on this hardware. Here is the updated plan.

---

## Frontend: Next.js First

The primary UI will be a **Next.js web app** running locally on your Mac, talking to a **Python FastAPI backend** that hosts the Sherpa-ONNX STT, Qwen3-14B LLM, grammar verifier, and VITS TTS pipeline. This is the fastest way to iterate on the UI — hot reload, React component dev tools, and easy Devanāgarī font/layout work in CSS.

**Architecture:**
```
Browser (localhost:3000)
  └── Next.js App (React + Tailwind)
        ├── WebSocket: live audio stream → STT
        ├── REST /translate: text → LLM → verifier → result JSON
        ├── REST /speak: text → TTS → audio blob
        └── WebSocket: vocal tract params (real-time VTL)

Python FastAPI Backend (localhost:8000)
  ├── /ws/audio  → Sherpa-ONNX STT
  ├── /translate → Qwen3-14B (llama-cpp-python or Ollama)
  ├── /verify    → SanskritShala / CLTK scorer
  ├── /speak     → VITS TTS
  └── /ws/vtl    → VocalTractLab real-time params
```

**Key tech choices for the frontend:**

| Concern | Choice | Reason |
|---|---|---|
| Framework | **Next.js 15 (App Router)** | SSR optional; great for local-first apps |
| Fonts | **Noto Sans Devanagari** (Google Fonts) | Best Unicode Sanskrit coverage |
| Audio | **Web Audio API + MediaRecorder** | Native browser mic access, no dependencies |
| Websockets | **native WebSocket + `ws` on server** | Low-latency audio streaming |
| 3D Visuals | **Three.js or React Three Fiber** | Renders VTL output in browser, no Unity needed |
| Styling | **Tailwind CSS v4** | Fast design iteration |

---

## What Changes (Everything Important)

### 🟢 1. Model Tier: Upgrade from 4B to 8B or 14B — No Compromise Needed

The original plan chose Qwen3-4B specifically because "4B fits in 4–8GB VRAM on modern laptops." On a 96GB unified memory M2 Max, this constraint **does not exist**.

| Model | 4-bit GGUF Size | Tokens/sec (M2 Max est.) | Use Case |
|---|---|---|---|
| Qwen3-4B | ~2.5 GB | ~80–100 tok/s | Was the target — now a fallback |
| **Qwen3-14B** | **~8 GB** | **~30–45 tok/s** | ✅ **New primary model** |
| Llama 3.1 8B | ~5 GB | ~50–70 tok/s | Good alternative |
| Qwen3-30B | ~18 GB | ~12–20 tok/s | Stretch goal / quality ceiling |

**Recommendation:** Use **Qwen3-14B-Instruct (Q4_K_M)** as the primary model. At ~8GB it uses less than 10% of available unified memory, leaving 88GB for everything else. The quality uplift for Sanskrit grammar — especially complex sandhi and vibhakti in long sentences — is significant over the 4B variant.

You could even run **Qwen3-30B** locally for the highest possible Sanskrit grammar quality while still meeting your latency budget, since the M2 Max's 400 GB/s memory bandwidth means even the 30B model can sustain ~15-20 tokens/sec — comfortably within your 800ms window for a typical sentence.

---

### 🟢 2. Latency Budget: Dramatically Relaxed

With the M2 Max's memory bandwidth and 38 GPU cores running via Metal/CoreML:

| Stage | Previous Target | M2 Max Realistic |
|---|---|---|
| Silero VAD | ~1ms | ~0.5ms |
| STT (Moonshine-Small, not Tiny) | 80–150ms | **40–80ms** |
| Sandhi splitter | 5–15ms | ~2ms |
| LLM first token (14B, 4-bit, Metal) | 150–350ms | **80–180ms** |
| Paninian verifier | 20–80ms | ~10–30ms |
| TTS (VITS fine-tuned) | 50–150ms | **30–80ms** |
| **Total** | 305–745ms | **~165–375ms** |

**The 800ms NFR1 target is trivially achievable.** You can tighten it to **≤500ms** in the SRS and still ship comfortably. This also means the verifier can run **synchronously** (before audio plays, not after) — which simplifies the architecture considerably and lets you present the Devanāgarī text before the audio starts.

---

### 🟢 3. STT: Upgrade to Moonshine-Small or Whisper-Medium

The plan specified Moonshine-Tiny or Whisper-Tiny to save memory. On this machine, run **Moonshine-Small** or **Whisper-Medium** for noticeably better transcription accuracy — particularly for Sanskrit-influenced English pronunciation (aspirates, retroflex sounds that speakers may carry over).

---

### 🟢 4. TTS: Train a Full-Quality VITS Model, Not a Tiny One

With 5.32 TB of free SSD and 96 GB of RAM:
- You can store and train a **full-quality VITS model** on all available Sanskrit TTS data without any compression.
- Run the Piper training pipeline **locally** rather than farming it out to Colab or rented GPUs. Training a VITS voice on ~8–20 hours of data takes approximately 24–48 hours on an M2 Max — fully feasible as an overnight training run.
- You can store **multiple voice variants** (male/female, classical vs. Vedic intonation styles) without storage pressure.

---

### 🟢 5. Speculative Decoding: No Longer Necessary

The prior review recommended speculative decoding specifically to overcome the memory bandwidth bottleneck on 8GB mobile hardware. On the M2 Max with 400 GB/s bandwidth, this bottleneck does not exist. Even the 30B model generates tokens fast enough to meet the 500ms tightened SRS target.

**Remove speculative decoding from Phase I scope.** It adds engineering complexity with no benefit here.

---

### 🟢 6. Storage: No Sideloading or App Distribution Constraints Apply

The concern about App Store size limits (200MB OBB, 4GB expansion limit) was raised for mobile distribution. Since your primary development and likely primary-use platform is **this Mac**, those constraints don't apply. You have:
- 5.32 TB free → store every model variant flat on disk with no pressure
- Run the app as a native **macOS application** (Swift/SwiftUI or Electron) rather than a mobile app, at least for Phase I

If you eventually want a mobile companion app on iPhone or iPad, those concerns apply to that port — but for the Mac-native version being built here, ignore them.

---

### 🟡 7. VocalTractLab Visualization: Now Feasible in Real-Time

The previous recommendation was to drop Unity and VocalTractLab on mobile due to memory pressure. On the M2 Max, this reverses:
- You have 88+ GB of free RAM after loading the LLM
- The 38-core GPU running Metal can easily handle real-time 3D vocal tract rendering
- VocalTractLab has a Python API (`VocalTractLabApi`) that can drive articulatory parameters in real-time

**Recommendation:** On the macOS desktop version, implement the **full real-time VocalTractLab integration** in Phase III as originally envisioned. The mobile port (Phase IV) would still use pre-rendered SVG fallbacks.

---

### 🟡 8. Paninian Verifier: Can Now Run Synchronously

Previously: "run the verifier async, after audio plays, so it doesn't block the 800ms window."  
Now: the verifier adds ~10–30ms on M2 Max. Run it **synchronously**. This means:
1. Voice input → STT → Sandhi splitter → LLM translation → **Verifier** → TTS → Audio out
2. The Devanāgarī text with confidence band is shown **before** audio starts playing
3. No async state management complexity needed

---

## Updated SRS Non-Functional Requirements

| NFR | Original | Updated |
|---|---|---|
| NFR1: Latency | ≤800ms end-to-end | **≤500ms** end-to-end |
| NFR2: Cost | $0.00 recurring | $0.00 (unchanged) |
| NFR3: Privacy | No server storage | (unchanged) |
| NFR4: RAM | Min 8GB | **Min 16GB; Optimal: 32GB+** |
| NFR5: Storage | 5–10GB models | **~20–30GB** (multiple model variants) |
| NFR6: Platform | Android/iOS primary | **Next.js web app (local) primary; mobile Phase IV** |

---

## Updated Model Stack

```
┌─────────────────────────────────────────────────────────────┐
│  DEVELOPMENT MACHINE: Apple M2 Max · 96GB · macOS 26.2      │
├─────────────────────────────────────────────────────────────┤
│  STT         Sherpa-ONNX + Moonshine-Small      ~80MB       │
│  VAD         Silero VAD (ONNX)                  ~2MB        │
│  LLM         Qwen3-14B-Instruct Q4_K_M (GGUF)  ~8GB        │
│  Grammar     SanskritShala / CLTK (Apache 2.0)  ~50MB       │
│  TTS         VITS (fine-tuned Sanskrit)         ~300MB      │
│  Visuals     VocalTractLab Python API (real-time 3D)        │
├─────────────────────────────────────────────────────────────┤
│  Total footprint: ~8.5GB active RAM / ~20GB on disk         │
│  Free RAM remaining: ~87GB  ✅                              │
│  Free disk remaining: ~5.3TB ✅                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Revised Roadmap (Next.js First)

| Phase | Goal | Timeline |
|---|---|---|
| **Phase 0** | License matrix, corpus setup, DCS download, VAD + STT sanity test | 1 week |
| **Phase I** | Python FastAPI backend: STT + Qwen3-14B + grammar scorer + VITS TTS | 3 weeks |
| **Phase II** | **Next.js frontend**: voice input → Devanāgarī display, audio playback, confidence band UI | 3 weeks |
| **Phase III** | Real-time VocalTractLab visualization in-browser via Three.js / React Three Fiber | 3 weeks |
| **Phase IV** | macOS native app wrapper (Electron or Tauri) if desired | 2 weeks |
| **Phase V** | iOS/Android mobile port (ExecuTorch, smaller model tier, SVG fallbacks) | 6 weeks |

---

> **Bottom line:** Your M2 Max eliminates the three hardest constraints in the plan — RAM pressure, bandwidth bottleneck, and storage limits. Upgrade the model, tighten the latency target, and build macOS-native first. The mobile port is Phase IV, not the primary target.
