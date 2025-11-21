"""Agent request schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Input schema for the LangChain + MCP agent."""

    question: str = Field(..., description="User question for the agent to solve.")


__all__ = ["AgentRequest"]
