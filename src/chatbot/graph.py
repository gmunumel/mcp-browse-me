"""LangGraph-powered chatbot that can call MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any, Sequence

from langchain.agents import create_agent
from langchain.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.mcp.client.actions import run_client_action
from src.models import ChatState


class ChatbotGraph:
    """Class-based builder for the LangGraph chatbot executor."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        system_prompt: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.system_prompt = system_prompt or (
            "You are an assistant that can answer questions using MCP tools. "
            "Favor using the provided tools to collect information before responding."
        )
        self.tools = self._build_tools()
        self.agent = self._build_agent()
        self.executor = self._build_graph()

    @staticmethod
    def _run_action_sync(action: str, value: str) -> str:
        """Execute an MCP action synchronously inside the tool thread."""
        return asyncio.run(run_client_action(action, value))

    def _build_tools(self) -> Sequence[BaseTool]:
        """Create tool wrappers bound to run_client_action."""

        @tool
        def mcp_browse_files(path: str) -> str:
            """List files in a directory using the MCP browse_files tool."""
            return self._run_action_sync("browse_files", path)

        @tool
        def mcp_query_db(query: str) -> str:
            """Execute SQL against the configured Chinook database using MCP."""
            return self._run_action_sync("query_db", query)

        @tool
        def mcp_list_tables() -> str:
            """List database tables using the MCP list_tables tool."""
            return self._run_action_sync("list_tables", "")

        @tool
        def mcp_hello(name: str) -> str:
            """Greet someone using the MCP say_hello tool."""
            return self._run_action_sync("hello", name)

        @tool
        def mcp_goodbye(name: str) -> str:
            """Say goodbye using the MCP say_goodbye tool."""
            return self._run_action_sync("goodbye", name)

        return [mcp_browse_files, mcp_query_db, mcp_list_tables, mcp_hello, mcp_goodbye]

    def _build_agent(self) -> Any:
        llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
        return create_agent(
            model=llm, tools=self.tools, system_prompt=self.system_prompt
        )  # type: ignore

    def _build_graph(self) -> Any:
        def call_agent(state: ChatState) -> Any:
            # Agent expects {"messages": [...]} and returns {"messages": [...]}
            return self.agent.invoke(state)

        graph: StateGraph = StateGraph(ChatState)
        graph.add_node("agent", call_agent)
        graph.add_node("tools", ToolNode(self.tools))
        graph.add_edge(START, "agent")
        graph.add_conditional_edges(
            "agent",
            lambda state: "tools" if state["messages"][-1].tool_calls else END,
            {"tools": "tools", END: END},
        )
        graph.add_edge("tools", "agent")
        return graph.compile()


def build_chatbot_executor() -> Any:
    """Backward-compatible helper to obtain the compiled executor."""
    return ChatbotGraph().executor
