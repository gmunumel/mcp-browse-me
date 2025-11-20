#!/usr/bin/env python3
"""MCP Hello World Client (using official mcp package)."""

from __future__ import annotations

import asyncio
import logging
import sys

from src.mcp.client.actions import SUPPORTED_ACTIONS, run_client_action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _print_usage() -> None:
    supported = ", ".join(SUPPORTED_ACTIONS)
    print(
        "Usage: python src/mcp/client/main.py <action> <value>\n"
        f"Actions: {supported}\n"
        "Examples:\n"
        "  python src/mcp/client/main.py hello Alice\n"
        "  python src/mcp/client/main.py browse_files .\n"
        '  python src/mcp/client/main.py query_db "SELECT COUNT(*) FROM \\"Track\\";"\n'
        "\n"
        "(Or run PYTHONPATH=src/mcp python -m client.main ... if you prefer `-m`.)"
    )


async def main() -> None:
    """Main client function."""
    if len(sys.argv) != 3:
        _print_usage()
        sys.exit(1)

    action = sys.argv[1]
    value = sys.argv[2]
    logger.info("Starting MCP %s action with input: %s", action, value)

    try:
        response = await run_client_action(action, value)
    except ValueError as exc:
        logger.error("%s", exc)
        _print_usage()
        sys.exit(1)

    print(f"\nServer Response: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
