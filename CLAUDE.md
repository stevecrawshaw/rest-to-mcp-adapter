# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

REST-to-MCP Adapter is a Python library that converts REST API specifications (OpenAPI 3.x, Swagger 2.x) into MCP (Model Context Protocol) tools for AI agents. The library follows a 4-phase pipeline architecture:

1. **Ingestion & Normalization**: Load API specs and convert to canonical format
2. **MCP Tool Generation**: Generate MCP-compatible tool definitions
3. **Runtime Execution**: Execute actual REST API calls
4. **MCP Server**: Expose tools via JSON-RPC 2.0 protocol

## Development Commands

### Environment Setup

```bash
# Install uv package manager first (if not installed)
# See: https://docs.astral.sh/uv/getting-started/installation/

# Sync dependencies
uv sync

# Run the example ODS server
uv run ods_server.py
```

### Testing Commands

The project uses pytest for testing (configured in pyproject.toml):

```bash
# Run all tests
uv run python -m pytest

# Run specific test file
uv run python -m pytest tests/test_specific.py

# Run with verbose output
uv run python -m pytest -v

# Run with debug logging
uv run python -m pytest -v --log-cli-level=DEBUG
```

### Code Quality

The project uses Black and Ruff for code formatting and linting:

```bash
# Format code with Black (line length: 88)
uv run black adapter/

# Lint with Ruff
uv run ruff check adapter/

# Auto-fix with Ruff
uv run ruff check --fix adapter/
```

### Building and Installation

```bash
# Install in development mode
pip install -e .

# Build distribution
python -m build

# Install with optional dependencies
pip install -e ".[langchain]"
```

## Architecture

### Module Structure

```
adapter/
├── ingestion/          # Phase 1: Load API documentation
│   ├── base_loader.py      # Abstract base for loaders
│   └── loader_openapi.py   # OpenAPI/Swagger loader with $ref dereferencing
├── parsing/            # Phase 1: Normalize to canonical format
│   ├── canonical_models.py # Pydantic models (CanonicalEndpoint, etc.)
│   └── normalizer.py       # Converts OpenAPI → CanonicalEndpoint
├── mcp/                # Phase 2: Generate MCP tools
│   ├── tool_generator.py   # Main generator with auth param filtering
│   ├── schema_converter.py # Canonical → JSON Schema conversion
│   └── tool_registry.py    # Store & manage tools + endpoints
├── runtime/            # Phase 3: Execute API calls
│   ├── executor.py         # Main executor with retry logic
│   ├── request_builder.py  # Build HTTP requests from endpoints
│   ├── response.py         # Response models and processing
│   └── auth.py             # All auth handlers (NoAuth, BearerAuth, etc.)
└── server/             # Phase 4: MCP server
    ├── server.py           # JSON-RPC 2.0 MCP server
    ├── tool_provider.py    # Tool discovery
    ├── execution_handler.py # Tool execution
    └── transport.py        # stdio transport
```

### Key Design Patterns

#### Pipeline Architecture
Each phase is independent and can be used standalone. The canonical data model (`CanonicalEndpoint`) decouples ingestion from tool generation, making the system extensible.

#### Conditional Authentication
Authentication is only applied if `endpoint.security` is non-empty. This prevents "too many parameters" errors on public endpoints.

#### Hybrid Auth Parameter Filtering
The `ToolGenerator` filters auth parameters using three sources:
1. Default common auth params (signature, timestamp, api_key, etc.)
2. Auto-detected params from OpenAPI security schemes
3. Custom overrides via `auth_params` parameter

This keeps tool schemas clean while auth handlers manage authentication behind the scenes.

#### Tool Name Truncation
MCP enforces a 64-character limit on tool names. The generator intelligently truncates by:
- Removing version numbers (v1, v2, v3)
- Removing API keywords (api, sapi, rest)
- Preserving API prefix, HTTP method, and key path components

#### $ref Dereferencing
`OpenAPILoader` automatically dereferences all JSON Pointer references during load, with circular reference protection.

## Common Development Patterns

### Pattern 1: Quick Prototyping (Convenience Method)

```python
from adapter import ToolRegistry, MCPServer, APIExecutor, BearerAuth

# One-line registry creation
registry = ToolRegistry.create_from_openapi(
    source="https://api.example.com/openapi.json",
    api_name="example"
)

# Create server (endpoints auto-included from registry)
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="token")
)
server = MCPServer(
    name="Example Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor
)
server.run()
```

### Pattern 2: Production (Explicit Phases)

```python
from adapter import OpenAPILoader, Normalizer, ToolGenerator, ToolRegistry

# Phase 1: Load and normalize
loader = OpenAPILoader()
spec = loader.load("openapi.yaml")
auth_params = loader.extract_auth_parameters(spec)

normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Phase 2: Generate tools with auto-detected auth params
generator = ToolGenerator(
    api_name="myapi",
    auto_detected_auth_params=auth_params
)
tools = generator.generate_tools(endpoints)

# Phase 3: Store registry and endpoints
registry = ToolRegistry(name="My API")
registry.add_tools(tools)
registry.export_json("registry.json")

# Save endpoints separately for later execution
import json
with open("endpoints.json", "w") as f:
    json.dump([ep.model_dump() for ep in endpoints], f)
```

### Pattern 3: Pre-generated Registry (Fast Startup)

```python
from adapter import ToolRegistry, APIExecutor, MCPServer

# Load pre-generated registry (no OpenAPI fetch needed)
registry = ToolRegistry.import_json("registry.json")

# Load endpoints for execution
import json
from adapter.parsing import CanonicalEndpoint
with open("endpoints.json") as f:
    endpoints = [CanonicalEndpoint(**data) for data in json.load(f)]

# Create and run server
executor = APIExecutor(base_url="...", auth=auth)
server = MCPServer(
    name="Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)
server.run()
```

## Authentication Handlers

All authentication handlers are in `adapter/runtime/auth.py`:

- **NoAuth**: Public endpoints (no authentication)
- **APIKeyAuth**: API key in header or query parameter
- **BearerAuth**: Bearer token authentication
- **BasicAuth**: HTTP basic authentication
- **OAuth2Auth**: OAuth2 token flow

Custom auth handlers should extend `AuthHandler` and implement the `apply(headers, params)` method.

## Important Considerations

### When Endpoints Are Required

- **Tool browsing/export**: Endpoints NOT needed
- **MCP server with execution**: Endpoints REQUIRED
- **Direct API calls via executor**: Endpoints REQUIRED

The convenience method `ToolRegistry.create_from_openapi()` stores endpoints in the registry, so they don't need to be passed separately to `MCPServer`.

### OpenAPI $ref Resolution

The `OpenAPILoader` automatically dereferences all `$ref` pointers. Circular references are detected and prevented. External refs (URLs) are currently not supported for security reasons.

### Logging

The project logs to stderr to avoid interfering with stdio transport. Use environment variable `LOG_LEVEL` to control verbosity (DEBUG, INFO, WARNING, ERROR).

### Windows Compatibility

The project uses `uv run --directory` with absolute paths for portability across platforms. On Windows, use forward slashes or double backslashes in paths:
- ✅ `C:/Users/user/project`
- ✅ `C:\\Users\\user\\project`
- ❌ `C:\Users\user\project` (single backslashes can cause issues)

## Example Server Implementation

See `ods_server.py` for a complete example of building an MCP server for the West of England OpenDataSoft API. This demonstrates:

- Environment variable configuration
- Logging setup (to stderr)
- Using the convenience method for registry creation
- Public API configuration (NoAuth)
- Error handling and graceful shutdown

## Testing Strategy

- **Unit tests**: Test each component in isolation (loader, normalizer, generator, executor)
- **Integration tests**: Test complete pipeline (load → normalize → generate → execute)
- **Test files location**: `tests/` directory (configured in pyproject.toml)
- **Test naming**: `test_*.py` files, `Test*` classes, `test_*` functions

When writing tests, use Pydantic model validation to catch schema errors early.

## Common Issues and Solutions

### Tool Name Too Long
If a tool name exceeds 64 characters, it will be automatically truncated. The full path is preserved in `tool.metadata["path"]`.

### Auth Parameters in Tool Schema
If you see auth parameters (signature, timestamp, etc.) in the generated tool schema, ensure you're using `auto_detected_auth_params` in ToolGenerator or explicitly passing `auth_params`.

### Public API Rejecting Auth Headers
If a public API returns errors about unexpected parameters, ensure the endpoint's `security` field is empty. The executor only applies auth when `endpoint.security` is non-empty.

### Circular $ref References
If the OpenAPI spec has circular references, the loader may fail. Check the spec for reference cycles in components/schemas.

## Documentation Files

- **README.md**: Quick start and basic usage
- **ARCHITECTURE.md**: Detailed architecture and design decisions
- **LIBRARY_USAGE.md**: Advanced usage patterns and API reference
- **ODS_README.md**: Example MCP server documentation (in main README.md)
