"""Action request schema."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from src.mcp.client.actions import SUPPORTED_ACTIONS


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


__all__ = ["ActionRequest"]
