from __future__ import annotations

"""Environment configuration and Fail-Fast security hardening."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

from app.core.exceptions import ConfigurationError, SecurityHardeningError

# Load environment variables from .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Application settings and environment validation container."""

    gemini_api_key: str
    vault_key: str | None
    jarvis_token: str | None
    environment: str
    host: str
    port: int

    @classmethod
    def load_from_env(cls) -> Settings:
        """Loads and returns settings from the environment.

        Returns:
            Settings: Validated immutable application settings.
        """
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            vault_key=os.getenv("VAULT_KEY", "").strip() or None,
            jarvis_token=os.getenv("JARVIS_TOKEN", "").strip() or None,
            environment=os.getenv("ENVIRONMENT", "development").strip().lower(),
            host=os.getenv("HOST", "0.0.0.0").strip(),
            port=int(os.getenv("PORT", "8000")),
        )

    def validate_fail_fast(self) -> None:
        """Executes mandatory hardening and fail-fast validation routines.

        Raises:
            SecurityHardeningError: If secrets or critical variables are missing or insecure.
            ConfigurationError: If configurations violate operational boundaries.
        """
        if not self.gemini_api_key:
            raise SecurityHardeningError(
                "FAIL-FAST: GEMINI_API_KEY is not defined in the environment. "
                "Ensure a valid key is set in .env before starting the server."
            )

        if self.environment == "production":
            if not self.jarvis_token or len(self.jarvis_token) < 16:
                raise SecurityHardeningError(
                    "FAIL-FAST: In production, JARVIS_TOKEN must be at least 16 characters long."
                )

        if not (1 <= self.port <= 65535):
            raise ConfigurationError(f"FAIL-FAST: Invalid port configuration: {self.port}")


settings = Settings.load_from_env()
