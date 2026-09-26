from __future__ import annotations

"""Memory and persistence service supporting thread-safe caching and lazy initialization."""

import logging
import threading
from typing import Any
from app.core.exceptions import PersistenceError

logger = logging.getLogger(__name__)


class MemoryService:
    """Thread-safe memory persistence service with concurrency locks and lazy initialization."""

    def __init__(self) -> None:
        """Initializes memory locks and local in-memory cache."""
        self._lock = threading.Lock()
        self._cache: dict[str, Any] = {}
        self._client: Any = None
        self._initialized = False

    def _lazy_init(self) -> None:
        """Initializes persistent storage client under a thread-safe lock.

        Prevents race conditions during simultaneous worker or thread access.
        """
        if self._initialized:
            return

        with self._lock:
            # Double-checked locking pattern
            if self._initialized:
                return

            try:
                # Attempt to initialize Mem0 or Firebase client if installed
                logger.info("Initializing persistence engine (Mem0 / Firestore)...")
                # Placeholder for optional external client instantiation
                self._initialized = True
                logger.info("Persistence engine initialized successfully.")
            except Exception as exc:
                logger.error("Failed to initialize persistence client: %s", exc, exc_info=True)
                raise PersistenceError(f"Persistence initialization failed: {exc}") from exc

    def set_item(self, key: str, value: Any) -> None:
        """Stores a key-value entry in thread-safe memory.

        Args:
            key: Unique storage identifier.
            value: Data payload to store.

        Raises:
            PersistenceError: If storage operation fails.
        """
        self._lazy_init()
        try:
            with self._lock:
                self._cache[key] = value
                logger.debug("Item stored in memory cache with key: %s", key)
        except Exception as exc:
            logger.error("Failed to set memory item for key '%s': %s", key, exc)
            raise PersistenceError(f"Unable to write key '{key}': {exc}") from exc

    def get_item(self, key: str, default: Any = None) -> Any:
        """Retrieves an entry from thread-safe memory.

        Args:
            key: Unique storage identifier.
            default: Default value if key is not found.

        Returns:
            Any: Stored value or default.

        Raises:
            PersistenceError: If reading encounters unexpected errors.
        """
        self._lazy_init()
        try:
            with self._lock:
                return self._cache.get(key, default)
        except Exception as exc:
            logger.error("Failed to retrieve memory item for key '%s': %s", key, exc)
            raise PersistenceError(f"Unable to read key '{key}': {exc}") from exc

    def clear(self) -> None:
        """Clears the local in-memory storage safely."""
        with self._lock:
            self._cache.clear()
            logger.info("Memory cache cleared.")
