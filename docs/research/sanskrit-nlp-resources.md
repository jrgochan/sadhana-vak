# Sanskrit NLP Resources & Datasets

A curated list of the datasets, tools, and corpora relevant to this project, with their licenses noted.

---

## Corpora & Training Data

| Resource | Type | License | URL | Notes |
|---|---|---|---|---|
| **Digital Corpus of Sanskrit (DCS)** | Lemmatized, POS-tagged texts | CC-BY 3.0 | [github: OliverHellwig/sanskrit](https://github.com/OliverHellwig/sanskrit) | Primary gold-standard corpus for LLM evaluation |
| **IIT Madras Sanskrit TTS Dataset** | Audio (~3h) | Open | [iitm.ac.in/tts](https://www.iitm.ac.in/donlab/tts/) | Primary TTS training data; needs augmentation |
| **Wikisource Sanskrit recordings** | Audio | CC-BY-SA | [sa.wikisource.org](https://sa.wikisource.org) | Supplementary TTS training audio |
| **Sanskrit Treebank (Hellwig)** | Dependency parsed | CC-BY | HuggingFace / GitHub | Used for fine-tuning morphological scorer |

---

## Grammar & Analysis Tools

| Tool | License | Maintainer | Notes |
|---|---|---|---|
| **CLTK Sanskrit** | Apache 2.0 | CLTK Project | Primary verifier in production (✅ approved) |
| **SanskritShala** | MIT / Apache 2.0 | IIT-BHU | Neural + rule hybrid; good sandhi/compound analysis |
| **sanskrit_parser** | **GPLv3** | avinashvarna | Dev tooling only — not for distribution |
| **Sanskrit Heritage Engine** | **AGPL** | Gerard Huet / INRIA | Research reference; run locally, never in prod binary |
| **indic-transliteration** | MIT | Shriramana Sharma | IAST ↔ Devanāgarī ↔ SLP1 ↔ HK normalization |

---

## Speech Models

| Model | Task | License | Notes |
|---|---|---|---|
| **Moonshine-Small** | English STT | Apache 2.0 | Primary STT for English voice input |
| **Whisper Medium** | English STT | MIT | Alternative; slightly higher quality, slower |
| **IndicASR (AI4Bharat)** | Sanskrit/Indic STT | Apache 2.0 | Phase III — Sanskrit voice input |
| **Silero VAD** | Voice activity detection | MIT | Runs in browser via WASM (onnxruntime-web) |
| **Piper / VITS** | Sanskrit TTS | MIT | Fine-tune on IIT-Madras + Wikisource |

---

## Key References

- Pāṇini's Aṣṭādhyāyī (rules 3,959 sūtras) — the formal grammar oracle the verifier approximates
- Śikṣā literature — canonical Sanskrit phoneme inventory (used for TTS phoneme validation table)
- Hellwig 2010 — *Morphological Disambiguation of Classical Sanskrit* (baseline for morphological analysis accuracy targets)
