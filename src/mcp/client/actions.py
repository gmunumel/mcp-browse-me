"""Client actions for MCP Browse Me."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Awaitable, Callable

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SERVER_SCRIPT = PROJECT_ROOT / "src" / "mcp" / "server" / "fast_mcp_server.py"


async def call_hello_tool(session: ClientSession, name: str) -> str:
    """Call the say_hello tool with a name."""
    tools = await session.list_tools()
    logger.info("Available tools: %s", [tool.name for tool in tools.tools])

    result = await session.call_tool("say_hello", {"name": name})

    if result.content:
        content = result.content[0]
        text_content = content if isinstance(content, TextContent) else None
        if text_content:
            return text_content.text if text_content.text else ""
    return "No response content received"


async def call_goodbye_tool(session: ClientSession, name: str) -> str:
    """Call the say_goodbye tool with a name."""
    tools = await session.list_tools()
    logger.info("Available tools: %s", [tool.name for tool in tools.tools])

    result = await session.call_tool("say_goodbye", {"name": name})

    if result.content:
        content = result.content[0]
        text_content = content if isinstance(content, TextContent) else None
        if text_content:
            return text_content.text if text_content.text else ""
    return "No response content received"


async def call_browse_files_tool(session: ClientSession, path: str) -> str:
    """Call the browse_files tool with a path."""
    tools = await session.list_tools()
    logger.info("Available tools: %s", [tool.name for tool in tools.tools])

    result = await session.call_tool("browse_files", {"path": path})

    if result.content:
        content = result.content[0]
        text_content = content if isinstance(content, TextContent) else None
        if text_content:
            return text_content.text if text_content.text else ""
    return "No response content received"


async def call_query_db_tool(session: ClientSession, query: str) -> str:
    """Call the query_database tool with a SQL query."""
    tools = await session.list_tools()
    logger.info("Available tools: %s", [tool.name for tool in tools.tools])

    result = await session.call_tool("query_database", {"query": query})

    if result.content:
        content = result.content[0]
        text_content = content if isinstance(content, TextContent) else None
        if text_content:
            return text_content.text if text_content.text else ""
    return "No response content received"


ActionHandler = Callable[[ClientSession, str], Awaitable[str]]


ACTION_HANDLERS: dict[str, ActionHandler] = {
    "hello": call_hello_tool,
    "goodbye": call_goodbye_tool,
    "browse_files": call_browse_files_tool,
    "query_db": call_query_db_tool,
}


SUPPORTED_ACTIONS = tuple(ACTION_HANDLERS.keys())


async def run_client_action(action: str, value: str) -> str:
    """Run a client action by invoking the fast MCP server over stdio."""
    handler = ACTION_HANDLERS.get(action)
    if handler is None:
        raise ValueError(
            f"Unknown action '{action}'. Expected one of {SUPPORTED_ACTIONS}"
        )

    if not SERVER_SCRIPT.exists():
        raise FileNotFoundError(
            f"Could not find fast MCP server at {SERVER_SCRIPT}. "
            "Ensure the project structure is intact."
        )

    server_cmd = [sys.executable, str(SERVER_SCRIPT)]

    async with stdio_client(
        StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connected to MCP %s action handler", action)
            return await handler(session, value)
