import io
import asyncio
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.model_path = settings.TTS_MODEL_PATH
        self.voice = None
        
        try:
            from piper.voice import PiperVoice
            import os
            if os.path.exists(self.model_path) and os.path.exists(f"{self.model_path}.json"):
                self.voice = PiperVoice.load(self.model_path, f"{self.model_path}.json")
                logger.info(f"Piper TTS Service initialized targeting {self.model_path}")
            else:
                logger.warning(f"TTS Model not found at {self.model_path}. Using fallback stub.")
        except ImportError:
            logger.warning("piper-tts not installed. Using fallback TTS stub.")

    def _generate_dummy_wav(self) -> bytes:
        import struct
        # Generate a minimal valid 1-second WAV file (16kHz, 16-bit PCM, Mono) to prevent browser audio errors
        sample_rate = 16000
        num_samples = sample_rate
        audio_data = b'\x00\x00' * num_samples # 1 second of silence
        
        header = b'RIFF'
        header += struct.pack('<I', 36 + len(audio_data))
        header += b'WAVEfmt '
        header += struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        header += b'data'
        header += struct.pack('<I', len(audio_data))
        
        return header + audio_data

    async def generate_speech(self, sanskrit_text: str) -> tuple[bytes, list[dict]]:
        """
        Takes Sanskrit text, returns raw PCM/WAV audio bytes and an array of phoneme timings 
        for 3D lip-sync synchronization in React Three Fiber.
        """
        if self.voice:
            # We run the synchronous piper generation in a thread
            def _synthesize():
                # For piper, we synthesize to a WAV buffer
                wav_io = io.BytesIO()
                self.voice.synthesize(sanskrit_text, wav_io)
                audio_bytes = wav_io.getvalue()
                
                # In a full implementation, we would extract the phoneme durations from the model.
                # Piper's Python API doesn't expose durations natively without hooking the ONNX output,
                # so we estimate flat durations based on text length for now.
                estimated_phonemes = [{"phoneme": char, "duration_ms": 100} for char in sanskrit_text if char.strip()]
                return audio_bytes, estimated_phonemes
            
            return await asyncio.to_thread(_synthesize)

        # Fallback if no Piper model
        await asyncio.sleep(0.5) # Simulate TTS latency
        dummy_audio = self._generate_dummy_wav()
        
        # Output realistic-looking dummy phonemes for the 3D visualizer
        dummy_phonemes = [
            {"phoneme": char, "duration_ms": 80} for char in sanskrit_text if char.strip()
        ]
        if not dummy_phonemes:
            dummy_phonemes = [
                {"phoneme": "a", "duration_ms": 100},
                {"phoneme": "h", "duration_ms": 100},
                {"phoneme": "a", "duration_ms": 100},
                {"phoneme": "m", "duration_ms": 100}
            ]
            
        return dummy_audio, dummy_phonemes
