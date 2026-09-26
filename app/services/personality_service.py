from __future__ import annotations

"""Personality matrix management service with thread-safe adjustments."""

import logging
import threading
from typing import Mapping

logger = logging.getLogger(__name__)

DEFAULT_PERSONALITY: dict[str, int] = {
    "sarcasmo": 35,
    "formalidade": 85,
    "eficiencia": 95,
    "humor": 20,
    "tecnicismo": 90,
}


class PersonalityService:
    """Manages the dynamic personality matrix for J.A.R.V.I.S."""

    def __init__(self, initial_matrix: Mapping[str, int] | None = None) -> None:
        """Initializes personality traits with thread safety."""
        self._lock = threading.Lock()
        self._matrix = dict(initial_matrix or DEFAULT_PERSONALITY)

    def adjust_trait(self, trait: str, percentage: int) -> tuple[bool, str]:
        """Adjusts a specific trait within valid [0, 100] bounds.

        Args:
            trait: Name of personality trait.
            percentage: Target percentage level.

        Returns:
            tuple[bool, str]: Success flag and confirmation message.
        """
        trait_key = trait.strip().lower()
        bounded_value = max(0, min(100, int(percentage)))

        with self._lock:
            if trait_key not in self._matrix:
                return False, f"Parâmetro '{trait}' não reconhecido na matriz de personalidade."

            self._matrix[trait_key] = bounded_value
            logger.info("Personality trait '%s' updated to %d%%.", trait_key, bounded_value)
            return True, f"Matriz atualizada: {trait_key} definido em {bounded_value}%."

    def get_matrix(self) -> dict[str, int]:
        """Returns a snapshot copy of the current personality matrix."""
        with self._lock:
            return dict(self._matrix)

    def get_system_instructions(self) -> str:
        """Constructs system instructions derived from active personality weights.

        Returns:
            str: Customized system prompt.
        """
        with self._lock:
            sarcasm = self._matrix.get("sarcasmo", 35)
            formality = self._matrix.get("formalidade", 85)
            efficiency = self._matrix.get("eficiencia", 95)
            technical = self._matrix.get("tecnicismo", 90)

        return (
            "Você é o J.A.R.V.I.S., assistente de inteligência artificial de elite da Arquitetura Mark V. "
            "Chame o usuário respeitosamente de 'Senhor'. "
            f"Seus parâmetros atuais são: Formalidade {formality}%, Eficiência {efficiency}%, "
            f"Tecnicismo {technical}%, Sarcasmo refinado {sarcasm}%. "
            "Seja direto, técnico, resolutivo e nunca prolixo."
        )
