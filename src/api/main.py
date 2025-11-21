"""API server for MCP Browse Me."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.chatbot.graph import build_chatbot_executor
from src.logger import logger
from src.mcp.client.actions import run_client_action
from src.models import ActionRequest, ActionResponse, AgentRequest, AgentResponse
from src.settings import settings

settings.load_env()
app = FastAPI(title="MCP Browse Me API", version="0.1.0")


agent_executor = build_chatbot_executor()


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


@app.post("/agent", response_model=AgentResponse, tags=["agent"])
async def ask_agent(request: AgentRequest) -> AgentResponse:
    """Answer questions using a LangChain agent backed by MCP tools."""
    logger.info("Agent request: %s", request.question)
    try:
        result = await agent_executor.ainvoke(
            {"messages": [{"role": "user", "content": request.question}]}
        )
    except Exception as exc:
        logger.exception("Agent invocation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    messages = result.get("messages", [])
    answer = messages[-1].content if messages else ""
    logger.info("Agent answer: %s", answer)
    return AgentResponse(question=request.question, answer=str(answer))
