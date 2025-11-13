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

## Usage

### Running the Application

1. **Start the server**:

   ```bash
   python server/main.py

   or using fastmcp:

   python server/fast_mcp_server.py
   ```

2. **Start the client** (which will automatically start the server):

   ```bash
   python client/main.py <action> <your_name>
   ```

   `<action>` could be: _hello_, _goodbye_, _browse_files_, or _query_db_.

   Example:

   ```bash
   python client/main.py Alice
   ```

   Expected output:

   ```
   🎉 Server Response: Hello, Alice! Welcome to the MCP Hello World server! 🌍
   ```

3. **Query the Chinook database**:

```bash
   python client/main.py query_db "SELECT name, composer FROM track LIMIT 5;"
   ```

   The client starts `server/fast_mcp_server.py`, which loads `.env`, connects to the configured database, and returns the tabular results.

   > **Note:** PostgreSQL folds unquoted identifiers to lowercase, so table/column names from the Chinook script appear as `track`, `album`, `name`, etc. Use lowercase (or quote the exact lowercase spelling) when running your queries.

### Running Tests

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=server --cov=client
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
mypy server/ client/
```

## Architecture

### Server (`server/main.py`)

The MCP server implements:

- **HelloInput Model**: Pydantic model for input validation
- **list_tools Handler**: Returns available tools (hello tool)
- **call_tool Handler**: Processes tool calls and generates greetings
- **STDIO Transport**: Uses standard input/output for communication

### Client (`client/main.py`)

The MCP client implements:

- **Session Management**: Establishes connection with the server
- **Tool Discovery**: Lists available tools from the server
- **Tool Invocation**: Calls the hello tool with user-provided name
- **Error Handling**: Gracefully handles connection and call errors

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
6. Type check: `mypy server/ client/`

## License

MIT License - feel free to use this as a starting point for your own MCP applications.

## Next Steps

This is a basic Hello World example. You can extend it by:

- Adding more tools to the server
- Implementing resource providers
- Adding persistent storage
- Creating more sophisticated client interactions
- Adding authentication and security features
