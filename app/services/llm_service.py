from __future__ import annotations

"""LLM Service encapsulating Gemini API interactions with defensive error handling."""

import logging
from typing import Any
from app.core.config import settings
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class LLMService:
    """Manages LLM client initialization and prompt inference."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initializes the LLM service.

        Args:
            api_key: Optional Gemini API key. Defaults to settings.gemini_api_key.
        """
        self._api_key = api_key or settings.gemini_api_key
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the Google GenAI SDK client defensivel.

        Raises:
            LLMServiceError: If the SDK cannot be loaded or client creation fails.
        """
        if not self._api_key:
            logger.warning("LLMService initialized without GEMINI_API_KEY.")
            return

        try:
            # Attempt to import modern google-genai
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                self._client_type = "genai"
                logger.info("Google GenAI client initialized successfully.")
            except ImportError:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self._api_key)
                self._client = legacy_genai.GenerativeModel("gemini-2.0-flash")
                self._client_type = "legacy"
                logger.info("Legacy Google GenerativeAI client initialized successfully.")
        except Exception as exc:
            logger.error("Failed to initialize Google GenAI client: %s", exc)
            raise LLMServiceError(f"Client initialization failed: {exc}") from exc

    async def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generates a text completion for the provided prompt.

        Args:
            prompt: User message or prompt instructions.
            system_instruction: Optional system instruction override.

        Returns:
            str: Generated model response text.

        Raises:
            LLMServiceError: If inference fails or client is not configured.
        """
        if not self._client:
            raise LLMServiceError("LLM client is not configured. Check GEMINI_API_KEY.")

        try:
            if self._client_type == "genai":
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction
                
                response = self._client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=config or None,
                )
                return response.text or ""
            else:
                response = self._client.generate_content(prompt)
                return response.text or ""

        except Exception as exc:
            logger.error("Error during LLM inference: %s", exc, exc_info=True)
            raise LLMServiceError(f"LLM inference failure: {exc}") from exc
