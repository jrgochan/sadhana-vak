import asyncio
import logging
import numpy as np
from core.config import settings

logger = logging.getLogger(__name__)


class STTService:
    """
    Speech-to-Text using Sherpa-ONNX with the Moonshine-Small model.
    Accepts raw PCM audio (16kHz, 16-bit, mono) and returns transcribed text.
    """

    def __init__(self):
        self.sample_rate = settings.STT_SAMPLE_RATE
        self._recognizer = None
        self._load_model()

    def _load_model(self):
        try:
            import sherpa_onnx  # type: ignore
            model_dir = settings.STT_MODEL_DIR

            self._recognizer = sherpa_onnx.OfflineRecognizer.from_moonshine(
                preprocessor=f"{model_dir}/preprocess.onnx",
                encoder=f"{model_dir}/encode.int8.onnx",
                uncached_decoder=f"{model_dir}/uncached_decode.int8.onnx",
                cached_decoder=f"{model_dir}/cached_decode.int8.onnx",
                tokens=f"{model_dir}/tokens.txt",
                decoding_method="greedy_search",
                num_threads=4,
            )
            logger.info(f"STT: Moonshine-Small loaded from {model_dir}")
        except ImportError:
            logger.warning("sherpa_onnx not installed — STT will return placeholder text.")
            self._recognizer = None
        except Exception as e:
            logger.warning(f"STT model load failed ({e}) — using placeholder.")
            self._recognizer = None

    async def transcribe_audio_chunk(self, pcm_bytes: bytes) -> str:
        """
        Transcribes a raw PCM audio chunk.
        pcm_bytes: signed 16-bit little-endian, 16000 Hz, mono
        """
        if self._recognizer is None:
            # Placeholder until model files are present
            await asyncio.sleep(0.05)
            return "[STT model not loaded — check backend/models/moonshine-small/]"

        # Run the blocking sherpa-onnx call in a thread pool
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, self._transcribe_sync, pcm_bytes)
        return text

    def _transcribe_sync(self, pcm_bytes: bytes) -> str:

        # Convert bytes → float32 numpy array expected by sherpa-onnx
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        stream = self._recognizer.create_stream()
        stream.accept_waveform(self.sample_rate, samples)
        self._recognizer.decode_stream(stream)
        return stream.result.text.strip()
