"""Persistence helpers for chat sessions."""

from __future__ import annotations

import json
import os
from typing import Sequence
from uuid import UUID, uuid4

import psycopg
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict
from psycopg.rows import dict_row


class ChatStore:
    """Simple Postgres-backed storage for chat transcripts."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.environ.get("DATABASE_URL")
        if not self.dsn:
            raise ValueError("DATABASE_URL is required for chat storage.")
        self._ensure_table()

    def _connect(self) -> psycopg.Connection:
        if not self.dsn:
            raise ValueError("DATABASE_URL is required for database connection.")
        return psycopg.connect(self.dsn)

    def _ensure_table(self) -> None:
        """Create the chat table if it doesn't already exist."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS chat_threads (
            session_id UUID PRIMARY KEY,
            messages JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(create_sql)
            conn.commit()

    def new_session_id(self) -> UUID:
        """Return a new random session identifier."""
        return uuid4()

    def load_messages(self, session_id: UUID) -> list[BaseMessage]:
        """Retrieve stored messages for a session."""
        with self._connect() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT messages FROM chat_threads WHERE session_id = %s",
                (str(session_id),),
            )
            row = cur.fetchone()
        if not row:
            return []
        stored = row["messages"] or []
        return messages_from_dict(stored)

    def save_messages(self, session_id: UUID, messages: Sequence[BaseMessage]) -> None:
        """Persist the full message list for a session."""
        stored = [message_to_dict(m) for m in messages]
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_threads (session_id, messages)
                VALUES (%s, %s)
                ON CONFLICT (session_id)
                DO UPDATE SET messages = EXCLUDED.messages, updated_at = NOW();
                """,
                (str(session_id), json.dumps(stored)),
            )
            conn.commit()
