#!/usr/bin/env python3
"""
MCP Hello World Client (using official mcp package)
"""

import asyncio
import logging
import sys

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


async def main() -> None:
    """Main client function."""
    if len(sys.argv) != 3:
        print(
            "Usage: python client/main.py <action> <value>\n"
            "Actions: hello, goodbye, browse_files, query_db\n"
            "Examples:\n"
            "  python client/main.py hello Alice\n"
            "  python client/main.py browse_files .\n"
            '  python client/main.py query_db "SELECT COUNT(*) FROM \\"Track\\";"'
        )
        sys.exit(1)

    action = sys.argv[1]
    value = sys.argv[2]
    logger.info("Starting MCP %s action with input: %s", action, value)

    server_cmd = [sys.executable, "server/fast_mcp_server.py"]

    # Connect to server over stdio
    async with stdio_client(
        StdioServerParameters(command=server_cmd[0], args=server_cmd[1:])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Connected to MCP %s World Server", action)

            if action == "hello":
                response = await call_hello_tool(session, value)
            elif action == "goodbye":
                response = await call_goodbye_tool(session, value)
            elif action == "browse_files":
                response = await call_browse_files_tool(session, value)
            elif action == "query_db":
                response = await call_query_db_tool(session, value)
            else:
                logger.error("Unknown action: %s", action)
                sys.exit(1)

            print(f"\nServer Response: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
