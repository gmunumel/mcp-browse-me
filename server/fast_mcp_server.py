#!/usr/bin/env python3
"""
MCP Hello World Server implemented with fastmcp.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
from pathlib import Path
from typing import Iterable

import psycopg
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing_extensions import Annotated

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP(
    name="mcp-browse-me",
    version="1.0.0",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def load_env_file(env_path: Path) -> None:
    """Populate os.environ with values from a .env file."""
    if not env_path.exists():
        logger.info("No .env file found at %s", env_path)
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file(ENV_PATH)


class SayHelloArgs(BaseModel):
    """Input schema for the say_hello tool."""

    name: str = Field(..., description="The name of the person to greet.")


class SayGoodbyeArgs(BaseModel):
    """Input schema for the say_goodbye tool."""

    name: str = Field(..., description="The name of the person to bid farewell.")


class BrowseFilesArgs(BaseModel):
    """Input schema for the browse_files tool."""

    path: str = Field(..., description="The directory path to browse.")


@app.tool
async def say_hello(args: SayHelloArgs) -> str:
    """Return a friendly greeting."""
    logger.info("Generating greeting for: %s", args.name)
    return f"Hello, {args.name}!"


@app.tool
async def say_goodbye(args: SayGoodbyeArgs) -> str:
    """Return a friendly farewell."""
    logger.info("Generating farewell for: %s", args.name)
    return f"Goodbye, {args.name}!"


@app.tool
async def browse_files(args: BrowseFilesArgs) -> str:
    """Return a comma-separated list of files found at the given path."""
    path = Path(args.path).expanduser()
    logger.info("Browsing files at: %s", path)
    try:
        files = os.listdir(path)
    except FileNotFoundError:
        return f"The path '{path}' does not exist."
    except NotADirectoryError:
        return f"The path '{path}' is not a directory."
    except PermissionError:
        return f"Permission denied while accessing '{path}'."
    return f"Files at {path}: " + ", ".join(files)


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
            "DATABASE_URL is not set. Add it to .env or the environment before querying."
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


@app.tool
async def query_database(query: QueryArgument) -> str:
    """Run arbitrary SQL against the configured Chinook database."""
    logger.info("Executing SQL query")
    try:
        return await asyncio.to_thread(execute_sql, query)
    except Exception as exc:
        logger.exception("Failed to execute query: %s", exc)
        return f"Failed to execute query: {exc}"


def main() -> None:
    """Entrypoint for running the fastmcp server over stdio."""
    app.run()


if __name__ == "__main__":
    main()
