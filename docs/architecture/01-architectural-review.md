# Sadhana-Vak: Architectural Review & Improvement Suggestions

The plan is genuinely ambitious and well-structured. What follows is a deep critical review — the goal is to surface the hidden risks before you commit to them in code.

---

## 1. 🔴 The Paninian Verifier Is Overstated — Address This First

**The problem:** The plan bills `sanskrit_parser` as a reliable "verifier" that every LLM output *must pass*, but the library's own documentation says it is **still under active development** and explicitly acknowledges **over-generation and under-generation** of valid forms. Level 3 (morpho-syntactic / vākya analysis) — exactly what you need for sentence-level verification — is labeled "early experimental" or "not begun" for most constructions.

The Aṣṭādhyāyī was not designed to be run in reverse (from surface form → derivation path). Reversing it computationally is an open research problem. Framing the verifier as a hard gate that *blocks* output will produce frustrating UX: many valid Sanskrit sentences will be wrongly rejected, while some malformed ones may pass.

**Recommended improvements:**

- **Reframe the verifier as a *scorer*, not a gate.** Use it to produce a confidence band (e.g., `VALID / LIKELY_VALID / UNCERTAIN / FLAG`), and surface that band to the user rather than silently blocking output.
- **Layer in Gerard Huet's Sanskrit Heritage Engine** (INRIA / UoH). It has a more mature, specifically rule-derived morphological analyzer accessible via local API (the site is open-source). Use it as a second opinion.
- **Add SanskritShala** (released 2023, neural + rule hybrid) for the dependency parsing step — it handles sandhi, compound analysis, and vibhakti tagging at a production-ready level.
- **Distinguish the two tasks Panini actually covers** in IxRS requirements: *word validity* (morphological, Level 1) vs. *sentence validity* (syntactic, Level 3). Be honest in the SRS that Level 3 is probabilistic, not deterministic.

---

## 2. 🔴 The GPLv3 License Incompatibility Is a Showstopper

**The problem:** `sanskrit_parser` is listed as **GPLv3**. Every other component in your stack is Apache 2.0 or MIT. If you distribute a mobile app (Android/iOS) that links against GPLv3 code — even as a Python subprocess — the **entire app must be relicensed under GPLv3 and its full source published**. The App Store's distribution terms are widely considered incompatible with GPLv3 (Apple controls distribution; GPLv3 requires the user be able to replace binaries). This is not a theoretical risk; Apple has removed apps for this reason.

**Recommended improvements:**

- Evaluate **SanskritShala** (MIT/Apache) or **CLTK Sanskrit module** (Apache 2.0) as drop-in alternatives for morphological analysis.
- If `sanskrit_parser` is essential for a specific sub-feature, **isolate it completely** into a local server process with a REST interface. The app talks to the server only; the GPL "infection" stays within the daemon boundary (this is a network service exception under AGPL theory, but for GPL it may still be risky — consult a lawyer before shipping to stores).
- Add a **License Compatibility Matrix** to the SRS as a non-functional requirement. Every new dependency gets an entry.

---

## 3. 🟡 The 800ms Latency Budget Has No Budget Breakdown

**The plan states:** `NFR1: Total end-to-end ≤ 800ms`. This is achievable in principle — research shows well-optimized pipelines hitting 450–650ms on consumer hardware — but the plan never explains *how*.

**Rough math on a mid-range device (M2 MacBook / Snapdragon 8 Gen 3):**

| Stage | Realistic Target | Notes |
|---|---|---|
| STT (Moonshine-Tiny, streaming) | 80–150ms | First word latency matters |
| Sandhi splitting / normalization | 5–15ms | Pure deterministic, negligible |
| LLM (Qwen3-4B @ 4-bit, first token) | 150–350ms | Heavily hardware-dependent |
| Paninian verifier | 20–80ms | Depends on sentence length |
| TTS (VITS, first audio chunk) | 50–150ms | Streaming helps enormously |
| **Total** | **305–745ms** | Tight at the high end |

Key gap: **the LLM must stream tokens**, and the TTS must begin generating from the *first complete clause*, not the full sentence. The plan mentions "first audio bytes in <150ms for TTS" but doesn't address LLM streaming or pipeline parallelism. Without this, real-world latency will exceed 800ms on anything below a high-end phone.

**Recommended improvements:**

- Add explicit streaming architecture: LLM → partial sentence detection → TTS ingestion of clause-complete chunks.
- Add **Voice Activity Detection (VAD)** as a pre-stage (this is completely missing from the plan). Without a proper VAD (e.g., Silero VAD, ~1ms overhead), the STT will process silence and generate garbage.
- Convert `NFR1` into a latency budget table as a testable spec, not a single number.
- Mandate that the verifier runs **asynchronously** (post-playback, not blocking audio output) — showing a confidence indicator after the spoken output.

---

## 4. 🟡 The STT Stage Has a Sanskrit-Specific Gap

**The problem:** Moonshine and Whisper-Tiny are trained predominantly on English. Sanskrit speech recognition is a hard problem: long compound words, retroflex consonants, Vedic pitch-accent, sandhi across utterance boundaries. Whisper-Large-v3 has some multilingual ability, but the *tiny* variant almost certainly does not handle Sanskrit well.

**The real user flow:** The plan says "English-to-Sanskrit voice assistant" in the SRS Introduction, but FR1 implies Sanskrit voice input as well (voice-to-voice implies both directions). Clarify this.

**Recommended improvements:**

- If the input is **English** (user speaks English): Whisper-Tiny is perfectly suited. This is the simpler, safer scope.
- If the input is **Sanskrit** (user speaks Sanskrit): you need an Indic-specialized model. Look at **AI4Bharat's IndicASR** (wav2vec2-based, Apache 2.0) or the **Vakyansh** toolkit for Sanskrit. There are no well-tested Sanskrit ASR models at the `tiny` size class yet — be explicit about this.
- Consider adding **Sanskrit text input as a fallback mode** alongside voice input for the v1 SRS to de-risk.

---

## 5. 🟡 The TTS Stage Needs a Training Data Plan

**The problem:** The plan says "Multilingual VITS / Piper — pre-trained for Indic languages like Hindi, *adapted* for Sanskrit phonetics." This hand-waves over a significant gap. Hindi and Sanskrit share the Devanāgarī script but not phonology: Sanskrit has retroflex ṭ/ḍ, aspirates, the Vedic svarabhakti vowel, and anusvāra distinctions that Hindi collapses. A Hindi-trained VITS voice will sound noticeably wrong for Sanskrit.

**Recommended improvements:**

- Use the **IIT Madras TTS Sanskrit dataset** (available from IIT-M TTS project, open license) or the **Wikisource Sanskrit audio** corpus to fine-tune a VITS model before Phase I ends.
- Use **Piper's training pipeline** (well-documented, ~8h of data needed for passable quality) and budget 1–2 weeks of compute time explicitly in the Phase I roadmap.
- For Vedic pitch-accent (udātta/anudātta/svarita): accept that standard VITS cannot encode pitch-accent without architectural changes. Scope this explicitly to **classical Sanskrit** only for v1, and flag Vedic support as a Phase IV stretch goal.
- Add a reference corpus to the SRS (FR3-adjacent): the app should validate TTS output against a known phoneme inventory (the Śikṣā literature gives this canonically for Pāṇinian Sanskrit).

---

## 6. 🟡 The Prompt Engineering Strategy Is Absent

The plan discusses the LLM extensively but says nothing about *how* it will be prompted. This is one of the highest-leverage engineering decisions in the whole system.

**Problems with naive prompting:**
- A generic instruction-following model will hallucinate Sanskrit — generating plausible-looking but ungrammatical sandhi, wrong vibhakti, incorrect dhātu forms.
- Without a grammar-aware system prompt, the model has no Pāṇinian "north star."

**Recommended improvements:**

- Design a **structured output format**: prompt the LLM to return a JSON object with fields `{translation, word_analysis: [{pada, root, case, number, gender}], sandhi_steps}`. This makes the Paninian verifier's job well-defined and enables the articulatory visualization to know *which word* is being spoken.
- Consider **few-shot prompting with Pāṇinian gold examples** baked into the system prompt (the plan's data section could reference DCS — Digital Corpus of Sanskrit — sentence pairs).
- Evaluate **Sanskrit-specific fine-tuned models**: SanskritBERT, or the LLM fine-tuned on the Sanskrit Treebank. Qwen3-4B may outperform them at general reasoning but a PEFT-adapted model may be better for translation quality specifically.
- Document the system prompt as a **versioned artifact** in the repo, not as an implementation detail.

---

## 7. 🟠 The Visualization Layer Scope Is Underspecified

**TubeN / VocalTractLab** is listed as "Pre-rendered or local 3D." VTL is a *research* articulatory synthesizer — it is not a mobile UI library. Integrating it into a Unity app requires:
1. Porting or wrapping the VTL C++ API
2. Building a real-time parameter bridge from the TTS phoneme output → VTL gestural score
3. A Unity build pipeline for mobile

This is, conservatively, a **3–6 month parallel workstream** for a single developer and should be its own phase with its own risk register.

**Recommended improvements:**

- For Phase I/II: Replace the VTL integration with **pre-rendered SVG cross-sections** of the vocal tract, one per phoneme class (you only need ~15 archetypes for Sanskrit's full inventory). This is a weekend of design work, not 3 months.
- For Phase III: Use VTL's Python bindings to pre-render the gestural animations offline, export them as sprite sheets or video clips keyed by phoneme, and play them back on demand. This is far lighter than a real-time C++ integration.
- Add a **Phoneme Mapping Table** to the SRS: for each Sanskrit phoneme (IAST), list the IPA, the VTL parameter target, and the sthāna/karaṇa classification. This table is the key data artifact for all three visualization phases.

---

## 8. 🟢 Missing Components Worth Adding

These are gaps in the plan that would surface early in implementation:

| Missing Component | Impact | Suggested Solution |
|---|---|---|
| **Voice Activity Detection (VAD)** | Without it, STT runs on silence | Silero VAD (MIT, 1MB, runs in 1ms) |
| **Transliteration normalization** | User may type IAST, HK, SLP1, Devanāgarī | `indic-transliteration` library (Apache 2.0) — better maintained than aksharamukha for this task |
| **Session memory / conversation context** | The verifier and LLM need to agree on `anaphora` across turns | A lightweight local vector store (e.g., Chroma with ONNX embeddings) |
| **Vedic pitch-accent encoding** | Plan mentions "Vedic intonations" but current TTS can't encode them | Descope to classical Sanskrit for v1; add SSML pitch control as Phase IV |
| **Offline model update mechanism** | User needs to update model weights without internet | Delta-patch system (e.g., `binary_delta` over local Wi-Fi) |
| **CI/CD & test suite strategy** | No mention of how to test Sanskrit output quality | BLEU on DCS gold pairs; TER on morphological tags; automated per-sutra regression tests |

---

## Revised Recommended Stack

```
┌──────────────────────────────────────────────────────────────────┐
│  INPUT LAYER                                                     │
│  Silero VAD (MIT) → Sherpa-ONNX STT                             │
│    If English input: Moonshine-Tiny (Apache 2.0)                │
│    If Sanskrit input: IndicASR / Vakyansh (Apache 2.0) [Phase II]│
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  TRANSLATION + ANALYSIS LAYER                                    │
│  Qwen3-4B-Instruct GGUF (Apache 2.0)                            │
│    Structured JSON output: translation + word analysis           │
│    System prompt: versioned, grammar-constrained, few-shot        │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  VERIFICATION LAYER (async, post-audio)                          │
│  SanskritShala or CLTK Sanskrit (Apache 2.0)  ← replace GPLv3   │
│    Morphological scoring (not blocking gate)                     │
│    Output: confidence band surfaced in UI                        │
│  Sanskrit Heritage Engine API (local, AGPL — research use only)  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  OUTPUT LAYER                                                    │
│  VITS/Piper fine-tuned on Sanskrit corpus (MIT)                  │
│    Streaming: clause-chunk → TTS immediately                     │
│    Devanāgarī + IAST display via indic-transliteration           │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  VISUALIZATION LAYER                                             │
│  Phase I: SVG pre-rendered vocal tract (15 phoneme archetypes)   │
│  Phase III: VTL offline pre-rendered sprite sheets               │
│  Phase IV: VTL real-time parameter bridge                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Revised Phased Roadmap

| Phase | Goal | Key Deliverables | Risk |
|---|---|---|---|
| **Phase 0** (2 weeks) | Foundation & Legal | License matrix, Sanskrit phoneme table, VAD + STT sanity tests, DCS gold test set | GPLv3 resolution |
| **Phase I** (6 weeks) | Core English→Sanskrit | Qwen3-4B + structured prompt, CLTK verifier as scorer, Piper TTS | LLM hallucination rate |
| **Phase II** (4 weeks) | Mobile Port | ExecuTorch export, Sherpa-ONNX packaging, SVG vocal tract UI | ExecuTorch model compat |
| **Phase III** (6 weeks) | Sanskrit Voice Input | IndicASR integration, Sanskrit text fallback, VTL sprite sheet visualization | ASR quality |
| **Phase IV** (ongoing) | Vedic & Advanced | Pitch-accent TTS, full Aṣṭādhyāyī coverage, real-time VTL | Open research |

---

## Summary of Critical Issues

| Severity | Issue | Consequence if Ignored |
|---|---|---|
| 🔴 Critical | GPLv3 license in core stack | App Store rejection, legal exposure |
| 🔴 Critical | Verifier presented as hard gate on immature library | Broken UX, poor user trust |
| 🟡 High | No VAD in pipeline | STT processing silence, garbled output |
| 🟡 High | Latency budget lacks streaming architecture spec | NFR1 will be violated on mid-range devices |
| 🟡 High | Hindi-trained TTS used for Sanskrit without fine-tuning | Poor pronunciation, especially retroflex phonemes |
| 🟡 High | No prompt engineering strategy | High hallucination rate for grammar |
| 🟠 Medium | VTL integration scoped as a single bullet point | 3–6 month scope surprise |
| 🟢 Low | Missing CI/CD and Sanskrit quality metrics | Hard to measure progress or regression |
