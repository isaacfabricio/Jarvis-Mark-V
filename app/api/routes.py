from __future__ import annotations

"""API endpoints definition for health, telemetry, vault, weather, and intelligence services."""

import json
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import LLMServiceError, PersistenceError, SecurityHardeningError
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.personality_service import PersonalityService
from app.services.system_service import SystemService
from app.services.vault_service import VaultService
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")

# Service singletons
memory_service = MemoryService()
llm_service = LLMService()
vault_service = VaultService()
weather_service = WeatherService()
personality_service = PersonalityService()


# ---------------- Models ----------------
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


class VaultStoreRequest(BaseModel):
    """Payload to store encrypted record in Vault."""

    title: str = Field(..., min_length=1, description="Title identifier")
    content: str = Field(..., min_length=1, description="Secret content to encrypt")


class PersonalityAdjustRequest(BaseModel):
    """Payload to adjust personality matrix."""

    trait: str = Field(..., min_length=1, description="Trait name, e.g. sarcasmo, formalidade")
    percentage: int = Field(..., ge=0, le=100, description="Percentage level between 0 and 100")


# ---------------- System & Telemetry Routes ----------------
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Provides operational health status of the J.A.R.V.I.S. Core API."""
    return {"status": "healthy", "service": "J.A.R.V.I.S. Mark V"}


@router.get("/telemetry", status_code=status.HTTP_200_OK)
async def get_telemetry() -> dict[str, Any]:
    """Retrieves current hardware telemetry metrics."""
    return SystemService.get_telemetry()


# ---------------- LLM & Chat Routes ----------------
@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_completion(payload: ChatRequest) -> ChatResponse:
    """Executes a prompt completion through the LLM Service."""
    system_instruction = payload.system_instruction or personality_service.get_system_instructions()
    try:
        reply = await llm_service.generate_text(
            prompt=payload.prompt,
            system_instruction=system_instruction,
        )
        return ChatResponse(response=reply)
    except LLMServiceError as exc:
        logger.error("API Chat failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# ---------------- Memory Routes ----------------
@router.get("/memory/{key}", status_code=status.HTTP_200_OK)
async def read_memory(key: str) -> dict[str, Any]:
    """Retrieves a cached item from thread-safe persistence."""
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
    """Persists an item into thread-safe memory."""
    try:
        memory_service.set_item(key, payload.value)
        return {"status": "stored", "key": key}
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ---------------- Vault Routes ----------------
@router.post("/vault/store", status_code=status.HTTP_201_CREATED)
async def store_vault_secret(payload: VaultStoreRequest) -> dict[str, str]:
    """Encrypts and safely stores a secret in the encrypted Vault."""
    try:
        saved_path = vault_service.store_encrypted(payload.title, payload.content)
        return {"status": "success", "file": saved_path.name}
    except SecurityHardeningError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/vault/get/{title}", status_code=status.HTTP_200_OK)
async def retrieve_vault_secret(title: str) -> dict[str, str]:
    """Retrieves and decrypts a secret from the encrypted Vault."""
    try:
        content = vault_service.retrieve_decrypted(title)
        return {"status": "success", "title": title, "content": content}
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except SecurityHardeningError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# ---------------- Weather Routes ----------------
@router.get("/weather/{city}", status_code=status.HTTP_200_OK)
async def get_city_weather(city: str) -> dict[str, Any]:
    """Retrieves meteorological data for a designated city."""
    result = weather_service.get_weather(city)
    if isinstance(result, str):
        return {"city": city, "message": result}
    return {
        "city": result.city,
        "temperature_celsius": result.temperature_celsius,
        "description": result.description,
        "humidity_percent": result.humidity_percent,
    }


# ---------------- Personality Routes ----------------
@router.get("/personality", status_code=status.HTTP_200_OK)
async def get_personality_matrix() -> dict[str, int]:
    """Returns the active personality traits weights."""
    return personality_service.get_matrix()


@router.post("/personality", status_code=status.HTTP_200_OK)
async def adjust_personality_matrix(payload: PersonalityAdjustRequest) -> dict[str, Any]:
    """Adjusts a specific trait within the personality matrix."""
    success, msg = personality_service.adjust_trait(payload.trait, payload.percentage)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "success", "message": msg, "matrix": personality_service.get_matrix()}


# ---------------- Realtime WebSocket Hub ----------------
@router.websocket("/ws/{token_acesso}")
async def websocket_realtime_hub(websocket: WebSocket, token_acesso: str) -> None:
    """Manages full-duplex WebSocket connection for real-time HUD and agent dispatch."""
    # Validate token if configured in settings
    if settings.jarvis_token and token_acesso != settings.jarvis_token:
        logger.warning("Rejected unauthorized WebSocket connection attempt.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info("WebSocket client connected successfully.")

    try:
        # Send initial handshake with telemetry
        initial_payload = {
            "type": "telemetry",
            "data": SystemService.get_telemetry(),
            "personality": personality_service.get_matrix(),
        }
        await websocket.send_text(json.dumps(initial_payload))

        while True:
            raw_data = await websocket.receive_text()
            try:
                message_json = json.loads(raw_data)
                action = message_json.get("action")

                if action == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif action == "chat":
                    user_prompt = message_json.get("prompt", "")
                    sys_inst = personality_service.get_system_instructions()
                    answer = await llm_service.generate_text(user_prompt, sys_inst)
                    await websocket.send_text(json.dumps({"type": "chat_reply", "content": answer}))
                elif action == "telemetry":
                    await websocket.send_text(
                        json.dumps({"type": "telemetry", "data": SystemService.get_telemetry()})
                    )
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as exc:
        logger.error("Error during WebSocket communication: %s", exc)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
