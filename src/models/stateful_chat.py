"""Schemas for stateful chat interactions."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class StatefulChatRequest(BaseModel):
    """Add a user message to a chat session (creates one if absent)."""

    message: str = Field(..., description="User message to add to the conversation.")
    session_id: UUID | None = Field(
        default=None,
        description="Existing session identifier. If omitted, a new "
        "session is created.",
    )


class StatefulChatResponse(BaseModel):
    """Response containing the assistant reply and session id."""

    session_id: UUID
    answer: str


__all__ = ["StatefulChatRequest", "StatefulChatResponse"]
