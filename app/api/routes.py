from __future__ import annotations

"""API endpoints definition for health, telemetry, and intelligence services."""

import logging
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.exceptions import LLMServiceError, PersistenceError
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.system_service import SystemService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

# Singletons for services
memory_service = MemoryService()
llm_service = LLMService()


class ChatRequest(BaseModel):
    """Payload for LLM inference requests."""

    prompt: str = Field(..., min_length=1, description="Prompt text to process")
    system_instruction: str | None = Field(default=None, description="Optional system prompt")


class ChatResponse(BaseModel):
    """Response returned from LLM inference."""

    response: str
    status: str = "success"


class MemoryPayload(BaseModel):
    """Payload for setting items in memory."""

    value: Any = Field(..., description="Data to persist")


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Provides operational health status of the J.A.R.V.I.S. Core API.

    Returns:
        dict[str, str]: Health status descriptor.
    """
    return {"status": "healthy", "service": "J.A.R.V.I.S. Mark V"}


@router.get("/telemetry", status_code=status.HTTP_200_OK)
async def get_telemetry() -> dict[str, Any]:
    """Retrieves current hardware telemetry metrics.

    Returns:
        dict[str, Any]: Telemetry metrics snapshot.
    """
    return SystemService.get_telemetry()


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_completion(payload: ChatRequest) -> ChatResponse:
    """Executes a prompt completion through the LLM Service.

    Args:
        payload: Prompt request parameters.

    Returns:
        ChatResponse: Generated text output.

    Raises:
        HTTPException: On inference failure or unconfigured API keys.
    """
    try:
        reply = await llm_service.generate_text(
            prompt=payload.prompt,
            system_instruction=payload.system_instruction,
        )
        return ChatResponse(response=reply)
    except LLMServiceError as exc:
        logger.error("API Chat failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/memory/{key}", status_code=status.HTTP_200_OK)
async def read_memory(key: str) -> dict[str, Any]:
    """Retrieves a cached item from thread-safe persistence.

    Args:
        key: Memory key identifier.

    Returns:
        dict[str, Any]: Retrieved value.

    Raises:
        HTTPException: If key does not exist or retrieval fails.
    """
    try:
        val = memory_service.get_item(key)
        if val is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key '{key}' not found in memory.",
            )
        return {"key": key, "value": val}
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/memory/{key}", status_code=status.HTTP_201_CREATED)
async def write_memory(key: str, payload: MemoryPayload) -> dict[str, str]:
    """Persists an item into thread-safe memory.

    Args:
        key: Memory key identifier.
        payload: Storage value container.

    Returns:
        dict[str, str]: Success confirmation.

    Raises:
        HTTPException: If persistence fails.
    """
    try:
        memory_service.set_item(key, payload.value)
        return {"status": "stored", "key": key}
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
