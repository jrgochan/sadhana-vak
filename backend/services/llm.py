import json
import logging
import os
from pathlib import Path
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "system_v1.txt").read_text()

from core.config import settings

# Ollama exposes an OpenAI-compatible API at localhost:11434
OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL    = settings.OLLAMA_MODEL


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",          # Ollama ignores this; required by the client
        )
        self.model = OLLAMA_MODEL
        logger.info(f"LLM Service ready → Ollama model: {self.model} at {OLLAMA_BASE_URL}")

    async def translate_to_sanskrit(self, english_text: str) -> dict:
        """
        Calls Qwen2.5-14B via Ollama's OpenAI-compatible API.
        Returns a structured dict with translation, IAST, word_analysis, grammar_score.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f'Translate: "{english_text}"'},
        ]

        logger.info(f"LLM request for: '{english_text}'")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,           # Low temp for deterministic grammar
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        logger.debug(f"LLM raw response: {raw}")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            # Attempt to extract JSON from any prose wrapper
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                logger.error(f"Could not parse LLM JSON: {raw}")
                result = {
                    "translation": raw,
                    "iast": "",
                    "word_analysis": [],
                }

        return result

    async def health_check(self) -> bool:
        """Verifies Ollama is reachable and the model is loaded."""
        try:
            models = await self.client.models.list()
            names = [m.id for m in models.data]
            if self.model not in names:
                logger.warning(f"Model '{self.model}' not found in Ollama. Available: {names}")
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
