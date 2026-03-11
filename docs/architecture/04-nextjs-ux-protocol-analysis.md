# Sadhana-Vak: Web UX & Protocol Analysis

With the architecture shifting to a Next.js 15 frontend on localhost, the communication patterns between the browser and the Python FastAPI backend become the new critical path. Here is a deep dive into the UX, protocols, and browser constraints for this specific pipeline.

---

## 1. ⚡ Protocol Choice: WebRTC vs WebSockets

**The Problem:** The updated plan assumes passing audio blobs via `WebSocket` to the backend STT engine. In 2025, sending continuous audio over WebSockets (which run over TCP) introduces "Head-of-Line blocking." If a single packet drops on your local network, the TCP window halts until it is retransmitted, causing audible jitter and stalling the STT pipeline. 

**The Improvement:** 
- **Use WebRTC for the audio stream.** WebRTC operates over UDP, prioritizing speed over guaranteed delivery (ideal for AI audio). It also includes native browser echo cancellation and noise suppression, which are strictly necessary if the user isn't wearing headphones.
- **Architecture mapping:**
  - **Browser → Python Backend:** `aiortc` (Python WebRTC library) receives the microphone stream and pipes raw PCM audio directly to Sherpa-ONNX.
  - **Python Backend → Browser (Text):** Server-Sent Events (SSE) or a persistent WebSocket for JSON responses (Devanāgarī text, morphological tags, confidence scores).
  - **Python Backend → Browser (Audio):** The VITS TTS output can be sent back as an Opus-encoded stream over the same WebRTC data channel for instant playback.

---

## 2. 🧠 Push VAD to the Edge (The Browser)

**The Problem:** If you pump a constant WebRTC audio stream to the Python backend, the backend has to constantly run Silero VAD to figure out if you are speaking or just breathing. This wastes backend CPU cycles.

**The Improvement:**
- **Run Silero VAD strictly in the browser using WebAssembly (WASM).** 
- In 2025, ONNX Runtime Web can execute the 1MB Silero VAD model in the browser at ~1ms per 32ms audio chunk.
- **The UX flow:** The browser listens locally. *Only when WASM VAD detects speech* does it open the WebRTC channel and start streaming audio to the STT backend. When VAD detects silence (end of utterance), the browser sends an "end-of-stream" signal. This gives the backend a perfectly cropped audio file, maximizing STT accuracy and saving massive compute.

---

## 3. 👄 The 3D Lip-Sync Synchronization Problem

**The Problem:** Phase III introduces a 3D vocal tract in React Three Fiber (R3F). The backend generates TTS audio and sends it to the frontend. However, to animate the 3D model, the frontend needs to know *exactly which phoneme/viseme* is being spoken at *exactly which millisecond*. 

**The Improvement:**
- Do not attempt to analyze the audio waveform in the browser to guess the phonemes (this adds latency and is notoriously inaccurate for Sanskrit).
- **Modify the TTS Backend:** When VITS generates the audio, it already knows the phoneme alignment. Configure the Python VITS service to output a JSON array of `[phoneme, duration_ms]` alongside the audio blob.
- **Frontend execution:** The Next.js app receives the audio file and the phoneme timing array. When playback starts, an R3F `useFrame` hook reads the audio clock (`context.currentTime`) and interpolates the 3D morph targets on the avatar based on the exact phoneme timestamp from the backend.
- Libraries like `wawa-lipsync` or simply mapping the Sanskrit phonemes to the closest standard blendshapes (e.g., Apple ARKit VRM blendshapes) make this trivial.

---

## 4. 🪷 UI/UX: The "Confidence Band" Mechanic

The Paninian Verifier is now synchronous and acts as a scorer. The UX needs to reflect this elegantly.

**Recommended Component Design:**
When the LLM finishes translating (e.g., "Aham gacchāmi"), the verifier scores the sentence. The UI should display the Devanāgarī explicitly color-coded:

- 🟢 **Solid Green text:** "Panini Verified" (Found exact derivation path in the grammar engine).
- 🟡 **Dotted Yellow underline:** "Probable" (Grammar engine failed to find a full path, but LLM confidence is high or partial sandhi matched). User can hover/tap to see the morphological breakdown.
- 🔴 **Red wavy underline:** "Grammar Error" (Verifier found a strict morphological violation, e.g., mismatched puruṣa/vacana).

This turns the UI from a black box into an interactive educational tool.

---

## Updated Action Items for the Developer

1. Set up the Next.js audio capture using `getUserMedia` and explicitly enable browser-level `echoCancellation` and `noiseSuppression`.
2. Add `onnxruntime-web` to the `package.json` to load the Silero VAD model client-side.
3. On the Python side, use `FastAPI` + `aiortc` for the WebRTC audio ingestion, rather than standard WebSockets.
