"""LangGraph-powered chatbot that can call MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.mcp.client.actions import run_client_action
from src.models import ChatState


def _run_action_sync(action: str, value: str) -> str:
    """Execute an MCP action synchronously inside the tool thread."""
    return asyncio.run(run_client_action(action, value))


@tool
def mcp_browse_files(path: str) -> str:
    """List files in a directory using the MCP browse_files tool."""
    return _run_action_sync("browse_files", path)


@tool
def mcp_query_db(query: str) -> str:
    """Execute SQL against the configured Chinook database using MCP."""
    return _run_action_sync("query_db", query)


@tool
def mcp_list_tables() -> str:
    """List database tables using the MCP list_tables tool."""
    return _run_action_sync("list_tables", "")


@tool
def mcp_hello(name: str) -> str:
    """Greet someone using the MCP say_hello tool."""
    return _run_action_sync("hello", name)


@tool
def mcp_goodbye(name: str) -> str:
    """Say goodbye using the MCP say_goodbye tool."""
    return _run_action_sync("goodbye", name)


TOOLS = [mcp_browse_files, mcp_query_db, mcp_list_tables, mcp_hello, mcp_goodbye]


def build_chatbot_executor() -> Any:
    """Build and return a LangGraph executor wired with MCP tools."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=(
            "You are an assistant that can answer questions using MCP tools. "
            "Favor using the provided tools to collect information before responding."
        ),
    )  # type: ignore

    def call_agent(state: ChatState) -> Any:
        # Agent expects {"mes": [...]} and returns {"messages": [...]}
        return agent.invoke(state)

    graph: StateGraph = StateGraph(ChatState)
    graph.add_node("agent", call_agent)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        lambda state: "tools" if state["messages"][-1].tool_calls else END,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "agent")

    return graph.compile()
