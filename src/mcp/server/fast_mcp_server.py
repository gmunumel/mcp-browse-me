#!/usr/bin/env python3
"""
MCP Hello World Server implemented with fastmcp.
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

import psycopg
from fastmcp import FastMCP
from pydantic import Field
from typing_extensions import Annotated

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.logger import logger  # noqa: E402, pylint: disable=wrong-import-position
from src.settings import settings  # noqa: E402, pylint: disable=wrong-import-position

settings.load_env()

app = FastMCP(
    name="mcp-browse-me",
    version="1.0.0",
)


@app.tool
async def say_hello(
    name: Annotated[str, Field(description="The name of the person to greet.")],
) -> str:
    """Return a friendly greeting."""
    logger.info("[FAST-MCP] Generating greeting for: %s", name)
    return f"Hello, {name}!"


@app.tool
async def say_goodbye(
    name: Annotated[str, Field(description="The name of the person to bid farewell.")],
) -> str:
    """Return a friendly farewell."""
    logger.info("[FAST-MCP] Generating farewell for: %s", name)
    return f"Goodbye, {name}!"


@app.tool
async def browse_files(
    path: Annotated[str, Field(description="The directory path to browse.")],
) -> str:
    """Return a comma-separated list of files found at the given path."""
    resolved = Path(path).expanduser()
    logger.info("[FAST-MCP] Browsing files at: %s", resolved)
    try:
        files = os.listdir(resolved)
    except FileNotFoundError:
        return f"The path '{resolved}' does not exist."
    except NotADirectoryError:
        return f"The path '{resolved}' is not a directory."
    except PermissionError:
        return f"Permission denied while accessing '{resolved}'."
    return f"Files at {resolved}: " + ", ".join(files)


def format_rows(headers: Iterable[str], rows: list[tuple[object, ...]]) -> str:
    """Pretty-print tabular data."""
    header_list = [str(h) for h in headers]
    if not rows:
        return "Query executed successfully (no rows returned)."

    col_widths = [len(h) for h in header_list]
    for row in rows:
        for idx, value in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(str(value)))

    def format_row(row: Iterable[object]) -> str:
        return " | ".join(
            str(value).ljust(col_widths[idx]) for idx, value in enumerate(row)
        )

    lines = [format_row(header_list), "-+-".join("-" * w for w in col_widths)]
    max_rows = 25
    for row in rows[:max_rows]:
        lines.append(format_row(row))
    if len(rows) > max_rows:
        lines.append(f"... {len(rows) - max_rows} more rows truncated ...")
    return "\n".join(lines)


def execute_sqlite_query(database_url: str, query: str) -> str:
    """Execute a SQL query against a SQLite database."""
    raw_path = database_url.removeprefix("sqlite:///")
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = (PROJECT_ROOT / db_path).resolve()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        if cursor.description is None:
            conn.commit()
            return f"Query executed successfully. Rows affected: {cursor.rowcount}"
        rows = cursor.fetchall()
        headers = [col[0] for col in cursor.description]
        return format_rows(headers, [tuple(row) for row in rows])


def execute_postgres_query(database_url: str, query: str) -> str:
    """Execute a SQL query against a PostgreSQL database."""
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)  # type: ignore
            if cursor.description is None:
                conn.commit()
                return f"Query executed successfully. Rows affected: {cursor.rowcount}"
            rows = cursor.fetchall()
            headers = [col.name for col in cursor.description]
            return format_rows(headers, rows)


def execute_sql(query: str) -> str:
    """Dispatch execution based on the DATABASE_URL protocol."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to .env or "
            "the environment before querying."
        )
    if database_url.startswith("sqlite:///"):
        return execute_sqlite_query(database_url, query)
    if database_url.startswith("postgresql://") or database_url.startswith(
        "postgres://"
    ):
        return execute_postgres_query(database_url, query)
    raise ValueError(f"Unsupported DATABASE_URL scheme in '{database_url}'.")


QueryArgument = Annotated[
    str, Field(description="SQL query to execute against DATABASE_URL.")
]


def build_list_tables_query(database_url: str) -> str:
    """Return a SQL statement that lists tables for the configured database."""
    if database_url.startswith("sqlite:///"):
        return "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    if database_url.startswith("postgresql://") or database_url.startswith(
        "postgres://"
    ):
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name;"
        )
    raise ValueError(f"Unsupported DATABASE_URL scheme in '{database_url}'.")


@app.tool
async def query_database(query: QueryArgument) -> str:
    """Run arbitrary SQL against the configured Chinook database."""
    logger.info("[FAST-MCP] Executing SQL query: %s", query)
    try:
        return await asyncio.to_thread(execute_sql, query)
    except Exception as exc:
        logger.exception("Failed to execute query: %s", exc)
        return f"Failed to execute query: {exc}"


@app.tool
async def list_tables() -> str:
    """List tables in the configured database (SQLite or PostgreSQL)."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return "DATABASE_URL is not set."
    try:
        query = build_list_tables_query(database_url)
        return await asyncio.to_thread(execute_sql, query)
    except Exception as exc:
        logger.exception("Failed to list tables: %s", exc)
        return f"Failed to list tables: {exc}"


def main() -> None:
    """Entrypoint for running the fastmcp server over stdio."""
    app.run()


if __name__ == "__main__":
    main()
