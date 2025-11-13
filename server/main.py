#!/usr/bin/env python3
"""
MCP Hello World Server (using official mcp package)
"""

import asyncio
import logging
import os
from typing import Any, Sequence

from mcp.server import InitializationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities, TextContent, Tool, ToolsCapability

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the server
server = Server(name="hello-mcp", version="1.0.0")


# Define a tool that greets a user
async def say_hello_tool(name: str) -> str:
    """A tool that says hello to the given name."""
    logger.info("Generating greeting for: %s", name)
    return f"Hello, {name}!"


async def say_goodbye_tool(name: str) -> str:
    """A tool that says goodbye to the given name."""
    logger.info("Generating farewell for: %s", name)
    return f"Goodbye, {name}!"


async def browse_files_tool(path: str) -> str:
    """A tool that lists files in current directory."""
    logger.info("Browsing files at: %s", path)
    files = os.listdir(path)
    return f"Files at {path}: " + ", ".join(files)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="say_hello",
            description="Say hello to someone by name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the person to greet.",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="say_goodbye",
            description="Say goodbye to someone by name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the person to bid farewell.",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="browse_files",
            description="Browse files in a given directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to browse.",
                    },
                },
                "required": ["path"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> Sequence[TextContent]:
    """Handle tool calls."""
    if name == "say_hello":
        result = await say_hello_tool(arguments["name"])
        return [TextContent(type="text", text=result)]
    elif name == "say_goodbye":
        result = await say_goodbye_tool(arguments["name"])
        return [TextContent(type="text", text=result)]
    elif name == "browse_files":
        result = await browse_files_tool(arguments["path"])
        return [TextContent(type="text", text=result)]
    else:
        raise ValueError(f"Unknown tool: {name}")


# Run the server
async def main() -> None:
    """Main server function."""
    logger.info("Starting MCP Hello World Server...")
    initialization_options = InitializationOptions(
        server_name="hello-mcp",
        server_version="1.0.0",
        capabilities=ServerCapabilities(tools=ToolsCapability(listChanged=True)),
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, initialization_options=initialization_options
        )


if __name__ == "__main__":
    asyncio.run(main())
