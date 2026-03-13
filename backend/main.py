from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routes import router
from api.routes_studio import router as studio_router
from api.routes import llm_service, stt_service, tts_service
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-time offline Sanskrit voice-to-voice AI pipeline",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
)

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(router, prefix=settings.API_V1_STR)
app.include_router(studio_router, prefix=settings.API_V1_STR)



@app.get("/health")
async def health_check():
    """
    Live health check — verifies each model service is actually loaded.
    See SRS §4: '/health → Checks all models loaded'.
    """
    llm_ok  = await llm_service.health_check()
    stt_ok  = stt_service._recognizer is not None
    tts_ok  = tts_service.voice is not None

    # Import verifier directly to check CLTK availability
    from api.routes import verifier_service
    verifier_ok = getattr(verifier_service, "_cltk_available", False)

    all_ok = llm_ok and stt_ok and tts_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "all_ok": all_ok,
        "service": settings.PROJECT_NAME,
        "models": {
            "llm":      {"loaded": llm_ok,      "model":  settings.OLLAMA_MODEL, "url": settings.OLLAMA_BASE_URL},
            "stt":      {"loaded": stt_ok,      "path":   settings.STT_MODEL_DIR},
            "tts":      {"loaded": tts_ok,      "path":   settings.TTS_MODEL_PATH},
            "verifier": {"loaded": verifier_ok, "backend": "cltk" if verifier_ok else "heuristic-stub"},
        },
    }
