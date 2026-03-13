import asyncio
import logging
import sys
import os

# Ensure backend root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.stt import STTService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_stt")

async def main():
    logger.info("Initializing STT Service...")
    stt = STTService()
    
    # Check if a model is actually loaded or if it's running in fallback mode
    if stt._recognizer is None:
        logger.warning("Running STT in fallback mode without Moonshine models.")
    else:
        logger.info("STT Moonshine loaded successfully.")
    
    # Generate 1s of 16kHz dummy silence to run through the transcriptor
    sample_rate = 16000
    dummy_wav_bytes = (b'\x00\x00' * sample_rate)
    
    logger.info("Testing asynchronous transcription pipe...")
    result = await stt.transcribe_audio_chunk(dummy_wav_bytes)
    
    logger.info(f"STT Transcript output: '{result}'")
    
if __name__ == "__main__":
    asyncio.run(main())
