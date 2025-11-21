"""Optional Chroma-backed vector memory for chat recall."""

from __future__ import annotations

import os
from typing import Any, Sequence
from uuid import UUID, uuid4

import chromadb
from chromadb.api.types import IncludeEnum
from chromadb.config import Settings
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def _message_to_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return str(content)


class ChromaMemory:
    """Lightweight wrapper around Chroma's HTTP client (v0.5.x)."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "chat-history",
    ) -> None:
        if chromadb is None:
            raise RuntimeError("chromadb dependency is not installed.")
        # Settings keeps telemetry quiet and matches the OSS server defaults.
        settings = Settings(
            chroma_api_impl="rest",
            chroma_server_host=host,
            chroma_server_http_port=port,
            allow_reset=True,
            anonymized_telemetry=False,
        )
        # Pass host/port directly so HttpClient and settings agree (avoids
        # ValueError when env-supplied host differs from defaults).
        self.client = chromadb.HttpClient(host=host, port=port, settings=settings)
        # Touch the collection to force a connectivity check
        self.collection = self.client.get_or_create_collection(collection_name)

    @classmethod
    def from_env(cls) -> "ChromaMemory | None":
        """Instantiate if CHROMA_HOST/PORT are provided; otherwise return None."""
        if chromadb is None:
            return None
        host = os.environ.get("CHROMA_HOST") or "localhost"
        port_str = os.environ.get("CHROMA_PORT") or "8000"
        try:
            port = int(port_str)
        except ValueError:
            port = 8000
        return cls(host=host, port=port)

    def add_messages(self, session_id: UUID, messages: Sequence[BaseMessage]) -> None:
        """Index messages to Chroma for later recall."""
        docs: list[str] = []
        ids: list[str] = []
        metadatas: list[Any] = []
        for message in messages:
            if not isinstance(message, (HumanMessage, AIMessage)):
                continue
            text = _message_to_text(message).strip()
            if not text:
                continue
            docs.append(text)
            ids.append(f"{session_id}:{uuid4()}")
            metadatas.append({"session_id": str(session_id), "role": message.type})
        if not docs:
            return
        self.collection.add(documents=docs, ids=ids, metadatas=metadatas)

    def query(
        self, *, text: str, session_id: UUID | None = None, k: int = 4
    ) -> list[str]:
        """Return the most relevant snippets for the provided text."""
        where: Any = None
        if session_id is not None:
            where = {"session_id": str(session_id)}
        results = self.collection.query(
            query_texts=[text],
            n_results=k,
            where=where,
            include=[IncludeEnum.documents],
        )
        documents: list[list[str]] = results.get("documents", []) or []
        if not documents:
            return []
        return [doc for doc in documents[0] if doc]
