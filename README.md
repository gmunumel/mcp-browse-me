# MCP Browse Me - Hello World

A simple Model Context Protocol (MCP) "Hello World" application demonstrating basic client-server communication.

## Overview

This project implements a minimal MCP server that provides a "hello" tool and a client that connects to the server to call this tool. The server responds with a personalized greeting message.

## Features

- **MCP Server**: Provides a "hello" tool that generates personalized greetings
- **MCP Client**: Connects to the server and calls the hello tool
- **Input Validation**: Uses Pydantic for robust input validation
- **Comprehensive Testing**: Unit tests for both server and client components
- **Type Safety**: Full type annotations throughout the codebase

## Project Layout

```
├── data/                         # Chinook sample data
├── src/
│   ├── api/                      # FastAPI application that wraps the MCP client
│   └── mcp/
│       ├── client/               # Interactive MCP client logic
│       └── server/               # fastmcp + reference server implementations
├── docker-compose.yml            # Postgres + Chinook bootstrapper
├── pyproject.toml                # Project metadata and dependency list
└── README.md
```

## Setup

### Prerequisites

- Python 3.8 or higher
- uv (recommended) or pip for package management
- Docker + Docker Compose for the optional Chinook database

### Installation

1. Clone or navigate to the project directory:

   ```bash
   cd mcp-browse-me
   ```

2. Install dependencies using uv:

   ```bash
   uv sync
   ```

   Or using pip:

   ```bash
   pip install -e .
   ```

3. For development dependencies:

   ```bash
   uv sync --group dev
   ```

   Or using pip:

   ```bash
   pip install -e ".[dev]"
   ```

## Chinook Sample Database

This repository ships with the Chinook sample data in `data/Chinook_PostgreSql.sql` (ready for PostgreSQL) and `data/Chinook_Sqlite.sqlite`. A Docker Compose definition (`docker-compose.yml`) is provided to spin up a PostgreSQL instance that imports the dataset automatically.

### Start the database

```bash
docker compose up -d chinook-db
```

The container initializes with the `chinook` database, `chinook` user, and `chinook` password. The SQL script is loaded automatically on the first run. Confirm the container is healthy before connecting:

```bash
docker compose ps chinook-db
```

### Connect and query

Use `psql` inside the container to interact with the database:

```bash
docker compose exec chinook-db psql -U chinook -d chinook
```

Or run a one-off query:

```bash
docker compose exec chinook-db \
  psql -U chinook -d chinook \
  -c 'SELECT name, composer FROM track ORDER BY trackid LIMIT 5;'
```

You can also connect from local tools with the connection string `postgresql://chinook:chinook@localhost:5432/chinook`.

> **Tip:** PostgreSQL automatically lowercases unquoted identifiers, so Chinook tables/columns are stored as `album`, `track`, `artist`, etc. Reference them in lowercase (or quote the lowercase spelling) to avoid `relation ... does not exist` errors.

### Configure the MCP server

Create a `.env` file in the project root (already provided) with the connection string so the MCP server can query the database:

```env
DATABASE_URL=postgresql://chinook:chinook@localhost:5432/chinook
```

If you prefer SQLite, point the URL at `sqlite:///data/Chinook_Sqlite.sqlite`.

An `OPENAI_API_KEY` entry is already present in `.env` for future integrations—leave it populated with your own key if you plan to extend the project with OpenAI tooling.

## Usage

### Running the MCP Client

The CLI automatically launches `src/mcp/server/fast_mcp_server.py`, which loads `.env`, connects to the configured database, and executes the requested tool.

```bash
python src/mcp/client/main.py <action> <value>
```

`<action>` can be: `hello`, `goodbye`, `browse_files`, or `query_db`.

> Alternatively, run `PYTHONPATH=src/mcp python -m client.main <action> <value>` if you prefer the `-m` style command.

Examples:

```bash
python src/mcp/client/main.py hello Alice
python src/mcp/client/main.py browse_files .
python src/mcp/client/main.py query_db "SELECT name, composer FROM track LIMIT 5;"
```

> **Note:** PostgreSQL folds unquoted identifiers to lowercase, so table/column names from the Chinook script appear as `track`, `album`, `name`, etc. Use lowercase (or quote the exact lowercase spelling) when running your queries.

### FastAPI Endpoint

A lightweight API surfaces the same MCP actions over HTTP.

Start the server (after `uv sync`/`pip install -e .`):

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Invoke it with `curl`, HTTPie, or your HTTP client of choice:

```bash
curl -X POST http://127.0.0.1:8000/actions \
  -H "Content-Type: application/json" \
  -d '{"action":"hello","value":"Alice"}'
```

The response payload mirrors the CLI output:

```json
{
  "action": "hello",
  "value": "Alice",
  "response": "Hello, Alice!"
}
```

### Running Tests

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src/mcp --cov=src/api
```

Run specific test files:

```bash
pytest tests/test_server.py
pytest tests/test_client.py
```

### Development Tools

Format code:

```bash
black .
```

Sort imports:

```bash
isort .
```

Type checking:

```bash
mypy src
```

## Architecture

### Server (`src/mcp/server/fast_mcp_server.py`)

The fastmcp server exposes several tools:

- **say_hello / say_goodbye**: Friendly greetings with Pydantic validation
- **browse_files**: Sanitized directory listings with helpful error messages
- **query_database**: Executes SQL against the Chinook database (SQLite or PostgreSQL) based on `DATABASE_URL`
- **Environment bootstrap**: Loads `.env` automatically so CLI/API invocations share DB credentials

### Client (`src/mcp/client`)

The client package contains reusable action helpers (`actions.py`) and the CLI entry point (`main.py`):

- **Session Management**: Establishes STDIO sessions against the fastmcp server
- **Tool Discovery**: Logs available tools before dispatching a request
- **Shared Helpers**: `run_client_action` drives both the CLI and HTTP API layers
- **Error Handling**: Raises descriptive errors for unsupported actions and missing server scripts

### API (`src/api/main.py`)

The FastAPI service wraps the MCP client:

- **Validation**: Ensures incoming `action` values match the supported tool list
- **/actions Endpoint**: Executes MCP actions asynchronously and returns the text result
- **/health Endpoint**: Lightweight readiness probe for container orchestration

### Communication Flow

1. Client starts and launches the server as a subprocess
2. Client establishes STDIO-based communication with server
3. Client initializes MCP session
4. Client lists available tools
5. Client calls the "hello" tool with the provided name
6. Server validates input and generates greeting
7. Client receives and displays the response

## API Reference

### Hello Tool

**Name**: `hello`

**Description**: Say hello to someone by name

**Input Schema**:

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "The name of the person to greet"
    }
  },
  "required": ["name"]
}
```

**Output**: Text content with personalized greeting

## Testing

The project includes comprehensive unit tests:

### Server Tests (`tests/test_server.py`)

- Input model validation
- Tool listing functionality
- Tool call handling with various inputs
- Error handling for invalid tools and arguments

### Client Tests (`tests/test_client.py`)

- Successful tool calls
- Error handling scenarios
- Edge cases (empty names, connection errors)

### Test Fixtures (`tests/conftest.py`)

- Common test data and setup

## Contributing

1. Install development dependencies
2. Make changes
3. Run tests: `pytest`
4. Format code: `black .`
5. Sort imports: `isort .`
6. Type check: `mypy src`

## License

MIT License - feel free to use this as a starting point for your own MCP applications.

## Next Steps

This is a basic Hello World example. You can extend it by:

- Adding more tools to the server
- Implementing resource providers
- Adding persistent storage
- Creating more sophisticated client interactions
- Adding authentication and security features
