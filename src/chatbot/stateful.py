"""LangGraph-based stateful chatbot with persistent storage."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.chatbot.graph import ChatbotGraph
from src.chatbot.store import ChatStore
from src.chatbot.vector_memory import ChromaMemory
from src.logger import logger


def _last_ai_content(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            return content if isinstance(content, str) else str(content)
    return ""


@dataclass
class StatefulChatbot:
    """Wrapper that manages chat sessions, storage, and optional vector memory."""

    store: ChatStore
    executor: Any
    vector_memory: ChromaMemory | None = None

    async def chat(self, *, session_id: UUID | None, message: str) -> tuple[UUID, str]:
        """Append a user message, run the LangGraph executor, and persist state."""
        sid = session_id or self.store.new_session_id()

        history = await asyncio.to_thread(self.store.load_messages, sid)
        logger.info("Loaded %s prior messages for session %s", len(history), sid)

        working_messages: list[BaseMessage] = [*history, HumanMessage(content=message)]

        # Optionally enrich with vector context
        if self.vector_memory:
            try:
                recalled = await asyncio.to_thread(
                    self.vector_memory.query, text=message, session_id=sid
                )
            except Exception as exc:
                logger.warning("Chroma recall failed: %s", exc)
                recalled = []
            if recalled:
                working_messages.append(
                    SystemMessage(
                        content="Context from memory:\n" + "\n\n".join(recalled)
                    )
                )

        result = await self.executor.ainvoke({"messages": working_messages})
        updated_messages: list[BaseMessage] = result.get("messages", working_messages)

        # Persist all messages (including tool traces) to Postgres
        await asyncio.to_thread(self.store.save_messages, sid, updated_messages)

        # Push the latest human/assistant exchanges to Chroma
        if self.vector_memory:
            try:
                await asyncio.to_thread(
                    self.vector_memory.add_messages,
                    sid,
                    [
                        msg
                        for msg in updated_messages
                        if isinstance(msg, (HumanMessage, AIMessage))
                    ],
                )
            except Exception as exc:
                logger.warning("Chroma write failed: %s", exc)

        return sid, _last_ai_content(updated_messages)


def build_stateful_chatbot(
    store: ChatStore, vector_memory: ChromaMemory | None
) -> StatefulChatbot:
    """Factory to assemble a stateful chatbot with persistence
    and (optional) vector recall."""
    executor = ChatbotGraph().executor
    return StatefulChatbot(store=store, executor=executor, vector_memory=vector_memory)
