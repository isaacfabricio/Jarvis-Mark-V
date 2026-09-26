from __future__ import annotations

"""Vault service managing encrypted on-disk storage using AES-256 (Fernet)."""

import logging
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.exceptions import PersistenceError, SecurityHardeningError

logger = logging.getLogger(__name__)


class VaultService:
    """Manages encryption, storage, and retrieval of sensitive data records."""

    def __init__(self, vault_dir: Path | None = None) -> None:
        """Initializes the vault service and validates encryption keys.

        Args:
            vault_dir: Path to directory storing encrypted blobs. Defaults to 'vault_jarvis'.
        """
        self.vault_dir = vault_dir or Path("vault_jarvis")
        self._cipher: Fernet | None = None
        self._init_cipher()

    def _init_cipher(self) -> None:
        """Initializes the Fernet symmetric cipher."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        key = settings.vault_key
        if not key:
            logger.warning("VAULT_KEY is not defined. Encrypted memory functions are disabled.")
            return

        try:
            self._cipher = Fernet(key.encode("utf-8"))
            logger.info("Vault encryption cipher initialized successfully.")
        except Exception as exc:
            logger.error("Failed to initialize Vault cipher with provided key: %s", exc)
            self._cipher = None

    def store_encrypted(self, title: str, content: str) -> Path:
        """Encrypts and persists content to disk under the specified title.

        Args:
            title: Human-readable title or identifier.
            content: Secret payload text to encrypt.

        Returns:
            Path: Path to the written encrypted file.

        Raises:
            SecurityHardeningError: If cipher is not initialized.
            PersistenceError: If file writing fails.
        """
        if self._cipher is None:
            raise SecurityHardeningError("Vault is not configured. Missing or invalid VAULT_KEY.")

        safe_filename = f"{title.strip().replace(' ', '_').lower()}.enc"
        file_path = self.vault_dir / safe_filename

        try:
            encrypted_payload = self._cipher.encrypt(content.encode("utf-8"))
            file_path.write_bytes(encrypted_payload)
            logger.info("Successfully stored encrypted memory: %s", safe_filename)
            return file_path
        except Exception as exc:
            logger.error("Failed to write encrypted memory for '%s': %s", title, exc)
            raise PersistenceError(f"Vault write failure: {exc}") from exc

    def retrieve_decrypted(self, title: str) -> str:
        """Reads and decrypts a persisted memory by title.

        Args:
            title: Title identifier of the stored secret.

        Returns:
            str: Decrypted plaintext content.

        Raises:
            SecurityHardeningError: If cipher is not initialized.
            PersistenceError: If file is missing or corrupted.
        """
        if self._cipher is None:
            raise SecurityHardeningError("Vault is not configured. Missing or invalid VAULT_KEY.")

        safe_filename = f"{title.strip().replace(' ', '_').lower()}.enc"
        file_path = self.vault_dir / safe_filename

        if not file_path.exists():
            raise PersistenceError(f"Vault item '{title}' does not exist.")

        try:
            sealed_data = file_path.read_bytes()
            decrypted_data = self._cipher.decrypt(sealed_data)
            return decrypted_data.decode("utf-8")
        except InvalidToken as exc:
            logger.error("Tampered or invalid token for memory '%s'", title)
            raise PersistenceError(f"Decryption failed: corrupted token or mismatched key.") from exc
        except Exception as exc:
            logger.error("Failed to read/decrypt vault file '%s': %s", safe_filename, exc)
            raise PersistenceError(f"Vault read failure: {exc}") from exc
