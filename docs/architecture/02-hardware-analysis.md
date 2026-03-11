# Sadhana-Vak: Edge Hardware & Runtime Deep Dive

After a second, deeper analysis focusing specifically on the physics of running this on consumer edge devices in 2025/2026, I have identified three critical hardware-level bottlenecks in the plan that need to be addressed before development begins.

---

## 1. 🚨 The RAM Death-Pinch (LLM + Unity Clash)

**The Problem:** The SRS states a minimum of 8GB of RAM. Let's look at the memory accounting on a typical 8GB Android or iOS device:
- **OS & Background processes:** ~2.0 GB
- **Qwen3-4B (4-bit quantized):** ~2.5 GB
- **Sherpa-ONNX (STT + TTS models):** ~0.5 GB
- **Remaining for App UI & buffers:** ~3.0 GB

The Phase III roadmap proposes embedding **VocalTractLab via Unity (Unity as a Library)** into the native app. In 2025, spinning up the Unity runtime inside a native mobile app brings massive managed heap overhead, unpredictable garbage collection (GC) spikes, and heavy GPU context switching. If Unity is trying to render a 3D vocal tract in real-time right as the LLM requests maximum memory bandwidth to generate text, the OS will aggressively kill the app due to Out-Of-Memory (OOM) limits (e.g., iOS Jetsam).

**The Improvement:**
- **Kill the Unity requirement.** A 3D articulatory model is visually cool but architecturally fatal on an 8GB device already running a 4B parameter LLM.
- **Alternative:** Implement the vocal tract visualization using **native 2D Canvas (CoreGraphics / Android Canvas)** or pre-rendered sprite animations. If 3D is strictly necessary, use a lightweight runtime like **Google Filament** or raw OpenGL/Metal, which have near-zero overhead compared to Unity.

---

## 2. ⚡ The Memory Bandwidth Wall

**The Problem:** The plan sets an aggressive 800ms end-to-end latency budget (NFR1). However, LLM inference on edge devices is rarely bound by compute (TOPS); it is bound by **Memory Bandwidth (GB/s)**. Generating a single token requires reading the entire model weight matrix from RAM to the NPU/GPU.
On a base Apple M2 or a mid-range Snapdragon, bandwidth is roughly 100 GB/s. A 4-bit 4B model requires ~2.5GB per read. That means absolute peak theoretical generation is ~40 tokens/second, assuming zero OS overhead and zero thermal throttling.

**The Improvement:**
- Specifying "8GB RAM" in the SRS is insufficient. You must specify a minimum memory bandwidth tier (e.g., LPDDR5x) or restrict to modern NPUs.
- **Add Speculative Decoding** to the architecture. Train or distill a tiny ~100M parameter "draft" model that guesses the next 3-4 Sanskrit tokens, and use the 4B model only to verify them. This bypasses the memory bandwidth bottleneck and allows you to comfortably hit the 800ms latency target without melting the user's battery.

---

## 3. 🛠️ The Runtime Schizophrenia (ExecuTorch vs MLC-LLM)

**The Problem:** The plan contains a contradiction. In the "Offline Pipeline Architecture" section, it says the app uses **MLC-LLM**. But in the Phase II Roadmap, it says **"Export the model to ExecuTorch (.pte)"**.
These are two completely different execution philosophies.
- **MLC-LLM** uses machine learning compilation (Apache TVM) to compile a custom, hardware-agnostic runtime (Vulkan/Metal).
- **ExecuTorch** is Meta's native PyTorch C++ runtime that relies on specific hardware delegates (like Qualcomm Hexagon NPU or Apple CoreML).

You cannot easily mix them without doubling your binary size, and both handle memory buffering differently.

**The Improvement:**
- **Standardize on ExecuTorch.** Given that you are targeting mobile devices in late 2025/2026, ExecuTorch has seen massive first-party investment from Meta, Apple, and Qualcomm. It allows you to use `torchao` to quantize the model and natively target the Qualcomm Hexagon NPU on Android or CoreML on iOS, which will yield significantly lower battery drain than MLC-LLM's generic Vulkan approach.
- Update the architecture document to explicitly drop MLC-LLM and standardize your pipeline (LLM and grammar engine) on PyTorch ahead-of-time (AOT) compilation.

---

## Updated Verdict for the Developer

Your biggest risks are no longer just linguistic (Paninian parsing) or legal (GPLv3). Your primary engineering risk is **thermal and memory starvation**.
Drop Unity, standardize on ExecuTorch, and implement speculative decoding. If you do those three things, an 800ms offline Sanskrit conversational agent on an 8GB phone moves from "theoretically possible" to "reliably shippable."
