import asyncio
import base64
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay

from services.llm import LLMService
from services.verifier import VerifierService
from services.tts import TTSService
from services.stt import STTService

logger = logging.getLogger(__name__)
router = APIRouter()

llm_service = LLMService()
verifier_service = VerifierService()
tts_service = TTSService()
stt_service = STTService()

# In-memory store of peer connections
pcs: set[RTCPeerConnection] = set()
relay = MediaRelay()


class TranslateRequest(BaseModel):
    text: str
    register: str = "classical"  # "classical" | "vedic"

class TranslateResponse(BaseModel):
    input_english: str
    translation: str
    iast: str
    word_analysis: list[dict]
    grammar_score: dict


class SpeakRequest(BaseModel):
    sanskrit_text: str

class SpeakResponse(BaseModel):
    audio_b64: str          # Base64-encoded WAV/PCM audio
    phoneme_timings: list[dict]  # [{phoneme, duration_ms}] for 3D lip-sync


class TranscribeAndTranslateRequest(BaseModel):
    audio_pcm_b64: str      # Base64 string of raw 16kHz 16-bit PCM bytes
    register: str = "classical"


class OfferRequest(BaseModel):
    sdp: str
    type: str


@router.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    """
    Full pipeline: English text → LLM → Paninian verifier.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    logger.info(f"Translating: '{req.text}'")
    result = await llm_service.translate_to_sanskrit(req.text)
    grammar = verifier_service.score_grammar(result.get("translation", ""))

    return TranslateResponse(
        input_english=req.text,
        translation=result.get("translation", ""),
        iast=result.get("iast", ""),
        word_analysis=result.get("word_analysis", []),
        grammar_score=grammar,
    )


@router.post("/transcribe_and_translate", response_model=TranslateResponse)
async def transcribe_and_translate(req: TranscribeAndTranslateRequest):
    """
    Decodes base64 PCM audio → STT transcription → LLM translation → Verifier.
    """
    try:
        pcm_bytes = base64.b64decode(req.audio_pcm_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 payload")

    # 1. STT
    transcribed_text = await stt_service.transcribe_audio_chunk(pcm_bytes)
    if not transcribed_text.strip():
        raise HTTPException(status_code=400, detail="STT produced no text from the audio.")

    # 2. LLM Translation
    logger.info(f"Transcribed audio: '{transcribed_text}'. Sending to LLM...")
    result = await llm_service.translate_to_sanskrit(transcribed_text)
    
    # 3. Verifier
    grammar = verifier_service.score_grammar(result.get("translation", ""))

    return TranslateResponse(
        input_english=transcribed_text,  # Return what the STT actually heard
        translation=result.get("translation", ""),
        iast=result.get("iast", ""),
        word_analysis=result.get("word_analysis", []),
        grammar_score=grammar,
    )


@router.post("/speak", response_model=SpeakResponse)
async def speak(req: SpeakRequest):
    """
    TTS pipeline: Sanskrit text → VITS → returns audio + phoneme timings.
    """
    if not req.sanskrit_text.strip():
        raise HTTPException(status_code=400, detail="Sanskrit text cannot be empty.")

    logger.info(f"Synthesizing speech for: '{req.sanskrit_text}'")
    audio_bytes, phoneme_timings = await tts_service.generate_speech(req.sanskrit_text)

    return SpeakResponse(
        audio_b64=base64.b64encode(audio_bytes).decode("utf-8"),
        phoneme_timings=phoneme_timings,
    )


async def consume_audio_track(track):
    """
    Consumes WebRTC audio track, converts to PCM chunk, and passes to STT.
    This is a naive baseline for the VAD-triggered stream.
    """
    logger.info(f"Started consuming audio track: {track.id}")
    try:
        # In a real pipeline, we'd buffer up to a VAD boundary.
        # Since the frontend will use Silero VAD to only open the stream during speech,
        # we can just consume frames until the track ends (frontend stops it).
        frames = []
        while True:
            frame = await track.recv()
            # Convert WebRTC AudioFrame to raw PCM bytes (16-bit, 16kHz mono required by out STT)
            # Resampling is needed if the incoming frame is e.g., 48kHz
            # For this Phase II simple implementation, we assume the track is pre-formatted or 
            # we just accumulate it.
            # Convert to numpy array
            pcm_data = frame.to_ndarray().tobytes()
            frames.append(pcm_data)
    except Exception as e:
        logger.info(f"Track {track.id} ended or error: {e}")
        
    # Once track ends (e.g., frontend detects end of speech via VAD and closes it)
    if frames:
        full_audio = b"".join(frames)
        logger.info(f"Track closed. Sending {len(full_audio)} bytes to STT.")
        text = await stt_service.transcribe_audio_chunk(full_audio)
        logger.info(f"STT Output: {text}")
        # Note: In a full event-driven system, we'd push this via Websocket or SSE to frontend.
        # Alternatively, we just log it here and Phase III will fully wire the SSE return.


@router.post("/offer")
async def offer(params: OfferRequest):
    """
    WebRTC signaling endpoint to negotiate SDP.
    The frontend sends an offer, we reply with an answer.
    """
    offer = RTCSessionDescription(sdp=params.sdp, type=params.type)

    pc = RTCPeerConnection()
    pcs.add(pc)

    logger.info(f"Created RTCPeerConnection {pc}")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        logger.info(f"Track received: {track.kind}")
        if track.kind == "audio":
            # Spin off task to consume audio to STT
            asyncio.ensure_future(consume_audio_track(track))

            @track.on("ended")
            async def on_ended():
                logger.info(f"Track {track.kind} ended")

    # Handle offer
    await pc.setRemoteDescription(offer)
    
    # Create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
