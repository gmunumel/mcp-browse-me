"""API server for MCP Browse Me."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.chatbot.stateful import build_stateful_chatbot
from src.chatbot.store import ChatStore
from src.chatbot.vector_memory import ChromaMemory
from src.logger import logger
from src.mcp.client.actions import run_client_action
from src.models import (
    ActionRequest,
    ActionResponse,
    StatefulChatRequest,
    StatefulChatResponse,
)
from src.settings import settings

settings.load_env()
app = FastAPI(title="MCP Browse Me API", version="0.1.0")

chat_store = ChatStore()

vector_memory = ChromaMemory.from_env()

stateful_chatbot = build_stateful_chatbot(store=chat_store, vector_memory=vector_memory)


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    """Simple health endpoint for readiness probes."""
    return {"status": "ok"}


@app.post("/actions", response_model=ActionResponse, tags=["actions"])
async def execute_action(request: ActionRequest) -> ActionResponse:
    """Invoke the MCP client for the requested action/value pair."""
    logger.info("API request for action '%s'", request.action)
    try:
        response = await run_client_action(request.action, request.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ActionResponse(action=request.action, value=request.value, response=response)


@app.post("/agent", response_model=StatefulChatResponse, tags=["agent"])
async def stateful_agent(request: StatefulChatRequest) -> StatefulChatResponse:
    """Answer questions while persisting chat history to Postgres
    (and Chroma if set)."""
    if stateful_chatbot is None:
        raise HTTPException(
            status_code=500,
            detail="Stateful chatbot unavailable. Ensure DATABASE_URL "
            "is set and reachable.",
        )

    logger.info("Agent request (session=%s)", request.session_id or "new")
    try:
        session_id, answer = await stateful_chatbot.chat(
            session_id=request.session_id, message=request.message
        )
        logger.info(
            "Agent response (session=%s): %s",
            session_id,
            answer[:50] + ("..." if len(answer) > 50 else ""),
        )
    except Exception as exc:
        logger.exception("Stateful agent invocation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StatefulChatResponse(session_id=session_id, answer=answer)
