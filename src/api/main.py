"""API server for MCP Browse Me."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

from src.logger import logger
from src.mcp.client.actions import SUPPORTED_ACTIONS, run_client_action
from src.settings import settings

settings.load_env()
app = FastAPI(title="MCP Browse Me API", version="0.1.0")


class ActionRequest(BaseModel):
    """Input schema for action execution requests."""

    action: str = Field(
        ...,
        description="The MCP action to execute "
        f"(one of: {', '.join(SUPPORTED_ACTIONS)}).",
    )
    value: str = Field(..., description="Argument passed to the selected action.")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        """Ensure the action is one of the supported actions."""
        if value not in SUPPORTED_ACTIONS:
            supported = ", ".join(SUPPORTED_ACTIONS)
            raise ValueError(f"action must be one of: {supported}")
        return value


class ActionResponse(BaseModel):
    """Output schema for action execution responses."""

    action: str
    value: str
    response: str


class AgentRequest(BaseModel):
    """Input schema for the LangChain + MCP agent."""

    question: str = Field(..., description="User question for the agent to solve.")


class AgentResponse(BaseModel):
    """Output schema for agent responses."""

    question: str
    answer: str


@tool
async def mcp_browse_files(path: str) -> str:
    """List files in a directory using the MCP browse_files tool."""
    return await run_client_action("browse_files", path)


@tool
async def mcp_query_db(query: str) -> str:
    """Execute SQL against the configured Chinook database using MCP."""
    return await run_client_action("query_db", query)


@tool
async def mcp_list_tables() -> str:
    """List database tables using the MCP list_tables tool."""
    return await run_client_action("list_tables", "")


@tool
async def mcp_hello(name: str) -> str:
    """Greet someone using the MCP say_hello tool."""
    return await run_client_action("hello", name)


@tool
async def mcp_goodbye(name: str) -> str:
    """Say goodbye using the MCP say_goodbye tool."""
    return await run_client_action("goodbye", name)


TOOLS = [mcp_browse_files, mcp_query_db, mcp_list_tables, mcp_hello, mcp_goodbye]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=(
        "You are an assistant that can answer questions using MCP tools. "
        "Favor using the provided tools to collect information before responding."
    ),
)  # type: ignore


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    """Simple health endpoint for readiness probes."""
    return {"status": "ok"}


@app.post("/actions", response_model=ActionResponse, tags=["actions"])
async def execute_action(request: ActionRequest) -> ActionResponse:
    """Invoke the MCP client for the requested action/value pair."""
    logger.info("API request for action '%s'", request.action)
    try:
        response = await run_client_action(request.action, request.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ActionResponse(action=request.action, value=request.value, response=response)


@app.post("/agent", response_model=AgentResponse, tags=["agent"])
async def ask_agent(request: AgentRequest) -> AgentResponse:
    """Answer questions using a LangChain agent backed by MCP tools."""
    logger.info("Agent request: %s", request.question)
    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": request.question}]}
        )
    except Exception as exc:
        logger.exception("Agent invocation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    messages = result.get("messages", [])
    answer = messages[-1].content if messages else ""
    logger.info("Agent answer: %s", answer)
    return AgentResponse(question=request.question, answer=str(answer))
