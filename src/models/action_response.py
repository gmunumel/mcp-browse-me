"""Action response schema."""

from __future__ import annotations

from pydantic import BaseModel


class ActionResponse(BaseModel):
    """Output schema for action execution responses."""

    action: str
    value: str
    response: str


__all__ = ["ActionResponse"]
