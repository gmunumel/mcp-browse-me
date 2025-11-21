"""Shared chatbot-related state models."""

from __future__ import annotations

from typing import Any, TypedDict, Union

from langchain_core.messages import AnyMessage


class ChatState(TypedDict):
    """Simple state container for LangGraph execution."""

    messages: list[Union[AnyMessage, dict[str, Any]]]


__all__ = ["ChatState"]
