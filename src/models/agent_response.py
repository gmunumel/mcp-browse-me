"""Agent response schema."""

from __future__ import annotations

from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Output schema for agent responses."""

    question: str
    answer: str


__all__ = ["AgentResponse"]
