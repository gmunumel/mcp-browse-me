"""API server for MCP Browse Me."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.mcp.client.my_actions import SUPPORTED_ACTIONS, run_client_action

logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Browse Me API", version="0.1.0")


class ActionRequest(BaseModel):
    """Input schema for action execution requests."""

    action: str = Field(
        ...,
        description="The MCP action to execute "
        f"(one of: {', '.join(SUPPORTED_ACTIONS)}).",
    )
    value: str = Field(..., description="Argument passed to the selected action.")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        """Ensure the action is one of the supported actions."""
        if value not in SUPPORTED_ACTIONS:
            supported = ", ".join(SUPPORTED_ACTIONS)
            raise ValueError(f"action must be one of: {supported}")
        return value


class ActionResponse(BaseModel):
    """Output schema for action execution responses."""

    action: str
    value: str
    response: str


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
