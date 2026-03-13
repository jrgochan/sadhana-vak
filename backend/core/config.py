import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Sadhana-Vak AI Pipeline"
    API_V1_STR: str = "/api/v1"
    
    # Models (Local Paths)
    LLM_MODEL_PATH: str = os.getenv("LLM_MODEL_PATH", "./models/qwen3-14b-instruct.Q4_K_M.gguf")
    STT_MODEL_DIR: str = os.getenv("STT_MODEL_DIR", "./models/moonshine-base")
    TTS_MODEL_PATH: str = os.getenv("TTS_MODEL_PATH", "./models/vits-sanskrit.onnx")
    VAD_MODEL_PATH: str = os.getenv("VAD_MODEL_PATH", "./models/silero_vad.onnx")

    # Ollama LLM Backend — default model MUST match what docs/architecture/06-tech-stack.md specifies.
    # Approved model: Llama 3.1 8B (Available locally).
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_0")

    # Pipeline Tuning
    VAD_THRESHOLD: float = 0.5
    STT_SAMPLE_RATE: int = 16000
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        case_sensitive = True

settings = Settings()
