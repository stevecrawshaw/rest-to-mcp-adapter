# ODS Monitoring API Support

This document describes the monitoring endpoint functionality for the West of England Combined Authority OpenDataSoft MCP server.

## Overview

The OpenDataSoft API provides two separate API surfaces:

1. **Catalog API** (`/catalog/...`) - Public datasets, no authentication required
2. **Monitoring API** (`/monitoring/...`) - Analytics and usage data, requires API key authentication

The monitoring API mirrors the catalog API structure but exposes special monitoring datasets:
- `ods-api-monitoring` - API usage metrics and statistics
- `ods-datasets-monitoring` - Dataset access and download metrics

## The Challenge

The official OpenAPI specification at `/api/explore/v2.1/swagger.json` only documents the **catalog** endpoints. The monitoring endpoints follow the same pattern but are not included in the spec, making them invisible to automated tool generation.

### Example from minimal-analytics-example.py

```python
# Monitoring endpoint URL structure
ods_monitoring_api_base_parquet_url = (
    "https://opendata.westofengland-ca.gov.uk"
    "/api/explore/v2.1/monitoring/datasets/ods-api-monitoring/exports/parquet"
)

# Requires API key
api = {"apikey": ods_apikey}
response = nq.get(ods_monitoring_api_base_parquet_url, params={**where_filter, **api})
```

## The Solution

We implemented **automatic monitoring endpoint generation** by cloning catalog dataset endpoints and modifying them for monitoring access.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenAPI Spec                            │
│           (only contains /catalog/ endpoints)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  Load & Normalize            │
          │  (16 catalog endpoints)      │
          └──────────┬───────────────────┘
                     │
                     ├──────────────┬──────────────────┐
                     │              │                  │
                     ▼              ▼                  │
          ┌──────────────┐   ┌─────────────────┐     │
          │ Catalog      │   │ Monitoring      │     │
          │ Tools (16)   │   │ Generator       │     │
          └──────────────┘   └────────┬────────┘     │
                                      │              │
                                      ▼              │
                            ┌──────────────────┐     │
                            │ Clone & Modify   │     │
                            │ - Path: /catalog/│     │
                            │   → /monitoring/ │     │
                            │ - Add security   │     │
                            │ - Update names   │     │
                            └────────┬─────────┘     │
                                     │               │
                                     ▼               │
                          ┌──────────────────┐       │
                          │ Monitoring       │       │
                          │ Tools (10)       │       │
                          └────────┬─────────┘       │
                                   │                 │
                                   └────────┬────────┘
                                            │
                                            ▼
                                  ┌──────────────────┐
                                  │ Tool Registry    │
                                  │ (26 total tools) │
                                  └──────────────────┘
```

### Components

#### 1. `ods_monitoring_generator.py`

The `ODSMonitoringGenerator` class clones catalog endpoints to monitoring endpoints:

```python
from ods_monitoring_generator import ODSMonitoringGenerator

generator = ODSMonitoringGenerator()
monitoring_endpoints = generator.generate_monitoring_endpoints(catalog_endpoints)
```

**Transformations applied:**
- **Path**: `/catalog/datasets/{id}/...` → `/monitoring/datasets/{id}/...`
- **Name**: `export_records_parquet` → `monitoring_export_records_parquet`
- **Security**: `[]` → `[{"apikey": []}]`
- **Tags**: `["catalog", "export"]` → `["monitoring", "export"]`
- **Description**: Enhanced with usage guidance that explains when to use monitoring vs catalog tools, which datasets require monitoring tools, and authentication requirements

**Filtering logic:**
- Only clones dataset-specific operations (those with `{dataset_id}` in path)
- Skips catalog-level endpoints like `/catalog/datasets` (list all datasets)
- Generates 10 monitoring endpoints from 16 catalog endpoints

#### 2. `ods_auth_resolver.py`

The `ODSAuthResolver` determines which authentication to use:

```python
class ODSAuthResolver:
    AUTH_REQUIRED_DATASETS = {
        'ods-api-monitoring',
        'ods-datasets-monitoring',
    }

    AUTH_REQUIRED_KEYWORDS = {
        'monitoring',
        'analytics',
    }

    def resolve_auth(self, tool_name: str, arguments: Dict[str, Any]) -> AuthHandler:
        # Check dataset_id in arguments
        if arguments.get('dataset_id') in self.AUTH_REQUIRED_DATASETS:
            return self.api_key_auth

        # Check tool name keywords
        if any(kw in tool_name.lower() for kw in self.AUTH_REQUIRED_KEYWORDS):
            return self.api_key_auth

        return self.no_auth
```

**Resolution rules:**
1. If `dataset_id` matches monitoring datasets → use API key
2. If tool name contains "monitoring" or "analytics" → use API key
3. Otherwise → no authentication

#### 3. `ods_execution_handler.py`

The `ODSExecutionHandler` swaps authentication dynamically:

```python
class ODSExecutionHandler(ExecutionHandler):
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
        # Resolve required auth
        required_auth = self.auth_resolver.resolve_auth(tool_name, arguments)

        # Temporarily swap auth
        original_auth = self.executor.auth
        try:
            self.executor.auth = required_auth
            result = super().execute_tool(tool_name, arguments)
            return result
        finally:
            # Always restore
            self.executor.auth = original_auth
```

#### 4. `ods_server.py`

Integration in the main server:

```python
# Load catalog endpoints from OpenAPI
registry = ToolRegistry.create_from_openapi(
    source=config['openapi_url'],
    api_name="ods",
)

# Generate monitoring endpoints
monitoring_generator = ODSMonitoringGenerator()
catalog_endpoints = registry.get_all_endpoints()
monitoring_endpoints = monitoring_generator.generate_monitoring_endpoints(catalog_endpoints)

# Generate and add monitoring tools
tool_generator = ToolGenerator(api_name="ods", auto_detected_auth_params=['apikey'])
monitoring_tools = tool_generator.generate_tools(monitoring_endpoints)

for tool in monitoring_tools:
    registry.add_tool(tool)

# Store all endpoints
all_endpoints = catalog_endpoints + monitoring_endpoints
registry.set_endpoints(all_endpoints)
```

## Available Monitoring Tools

The following monitoring tools are automatically generated:

| Tool Name | Path | Description |
|-----------|------|-------------|
| `ods_monitoring_get_records` | `/monitoring/datasets/{dataset_id}/records` | Query monitoring dataset records |
| `ods_monitoring_export_records` | `/monitoring/datasets/{dataset_id}/exports/{format}` | Export monitoring data in any format |
| `ods_monitoring_export_records_csv` | `/monitoring/datasets/{dataset_id}/exports/csv` | Export as CSV |
| `ods_monitoring_export_records_parquet` | `/monitoring/datasets/{dataset_id}/exports/parquet` | Export as Parquet |
| `ods_monitoring_export_records_gpx` | `/monitoring/datasets/{dataset_id}/exports/gpx` | Export as GPX |
| `ods_monitoring_get_dataset` | `/monitoring/datasets/{dataset_id}` | Get monitoring dataset metadata |
| `ods_monitoring_get_records_facets` | `/monitoring/datasets/{dataset_id}/facets` | Get facet values |
| `ods_monitoring_get_dataset_attachments` | `/monitoring/datasets/{dataset_id}/attachments` | List attachments |
| `ods_monitoring_get_record` | `/monitoring/datasets/{dataset_id}/records/{record_id}` | Get single record |
| `ods_monitoring_list_dataset_export_formats` | `/monitoring/datasets/{dataset_id}/exports` | List export formats |

## Configuration

### Environment Variables

```bash
# Required for monitoring endpoints
ODS_API_KEY=your_api_key_here

# Optional (defaults shown)
ODS_BASE_URL=https://opendata.westofengland-ca.gov.uk/api/explore/v2.1
ODS_OPENAPI_URL=https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json
LOG_LEVEL=INFO
```

### MCP Server Configuration

Add to your Claude Code settings (`~/.config/claude/settings.yml` or Windows equivalent):

```yaml
mcpServers:
  west-england-ods:
    command: uv
    args:
      - run
      - --directory
      - /path/to/rest-to-mcp-adapter
      - python
      - ods_server.py
    env:
      ODS_API_KEY: "your_api_key_here"
      LOG_LEVEL: "INFO"
```

## Usage Examples

### Example 1: Query API Monitoring Data

```python
# Using the MCP tool
result = await call_tool(
    "ods_monitoring_export_records_parquet",
    {
        "dataset_id": "ods-api-monitoring",
        "where": "timestamp > date'2026-01-01'",
        "limit": 100
    }
)
```

### Example 2: Get Dataset Access Metrics

```python
result = await call_tool(
    "ods_monitoring_get_records",
    {
        "dataset_id": "ods-datasets-monitoring",
        "where": "download_count > 10",
        "order_by": "download_count desc",
        "limit": 20
    }
)
```

### Example 3: Export Yesterday's Analytics

```python
from datetime import datetime, timedelta

yesterday = (datetime.now() - timedelta(days=1)).date()

result = await call_tool(
    "ods_monitoring_export_records_parquet",
    {
        "dataset_id": "ods-api-monitoring",
        "where": f"timestamp > date'{yesterday}'"
    }
)
```

## Authentication Behavior

The system uses **conditional authentication**:

### Catalog Endpoints (Public)
```
Tool: ods_get_records
Arguments: {"dataset_id": "public-transport-data"}
Auth: NoAuth (public access)
Result: ✓ Success
```

### Monitoring Endpoints (Authenticated)
```
Tool: ods_monitoring_export_records_parquet
Arguments: {"dataset_id": "ods-api-monitoring"}
Auth: APIKeyAuth (apikey in query params)
Result: ✓ Success (if API key valid)
```

### Without API Key
```
Tool: ods_monitoring_export_records_parquet
Arguments: {"dataset_id": "ods-api-monitoring"}
Auth: NoAuth (no API key configured)
Result: ✗ 401 Unauthorized
```

## Testing

### Unit Tests

Run the monitoring generator tests:

```bash
uv run python -m pytest tests/test_ods_monitoring_generator.py -v
```

**Test coverage:**
- Endpoint filtering (dataset-specific vs catalog-level)
- Path modification
- Name generation
- Security addition
- Tag updates
- Parameter preservation
- Deep copy verification

### Integration Tests

Test the full conditional auth system:

```bash
uv run python -m pytest tests/test_ods_conditional_auth.py -v
```

### Manual Testing

Run the simple test script:

```bash
uv run python test_monitoring_simple.py
```

## Troubleshooting

### API Key Not Working

**Symptom:** 401 Unauthorized when calling monitoring endpoints

**Solutions:**
1. Check environment variable: `echo $ODS_API_KEY`
2. Verify API key has "browse analytics" permission in OpenDataSoft
3. Check server logs for "API key: present" message
4. Confirm tool name contains "monitoring" keyword

### Monitoring Tools Not Available

**Symptom:** Only 16 tools instead of 26

**Solutions:**
1. Check server startup logs for "Generated 10 monitoring endpoints"
2. Verify `ods_monitoring_generator.py` is in the repository
3. Check for import errors in server logs
4. Restart the MCP server

### Wrong Authentication Applied

**Symptom:** Public endpoint gets API key, or monitoring endpoint doesn't

**Solutions:**
1. Check `ODSAuthResolver` logs for auth decision
2. Verify tool name contains "monitoring" keyword
3. Check dataset_id matches `AUTH_REQUIRED_DATASETS`
4. Enable DEBUG logging: `LOG_LEVEL=DEBUG`

### Dataset Does Not Exist Error (Fixed in Jan 2026)

**Symptom:** Monitoring datasets return "The requested dataset ods-api-monitoring does not exist"

**Root Cause:**
This was a critical bug in `adapter/server/execution_handler.py:74-112` where the tool-to-endpoint mapping logic was incorrectly matching monitoring tools to catalog endpoints.

**The Problem:**
The original mapping logic used a simple suffix match:
```python
if tool.name == endpoint.name or tool.name.endswith(f"_{endpoint.name}"):
```

This caused:
- Tool: `ods_monitoring_get_records`
- To match: `get_records` (catalog endpoint) ❌
- Instead of: `monitoring_get_records` (monitoring endpoint) ✓

Because catalog endpoints came first in the list, they were matched first, sending requests to `/catalog/datasets/ods-api-monitoring/records` instead of `/monitoring/datasets/ods-api-monitoring/records`.

**Debug Evidence:**
```
Request URL: .../catalog/datasets/ods-api-monitoring/records  # Wrong!
Status: 404 - dataset does not exist
```

Should be:
```
Request URL: .../monitoring/datasets/ods-api-monitoring/records  # Correct!
Status: 200 - 368,883 records available
```

**The Fix:**
Updated `_build_tool_endpoint_map()` to use **longest-match** logic:
```python
# Prefer longer matches to avoid false positives
# e.g., "ods_monitoring_get_records" should match "monitoring_get_records"
# not "get_records"
if len(endpoint.name) > best_match_length:
    best_match = endpoint
    best_match_length = len(endpoint.name)
```

**Testing:**
To verify monitoring endpoints are working correctly:

1. **Test direct API access:**
```python
import requests
response = requests.get(
    'https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/monitoring/datasets/ods-api-monitoring/records',
    params={'apikey': 'YOUR_KEY', 'limit': 5}
)
print(f"Status: {response.status_code}")  # Should be 200
```

2. **Run debug script:**
```bash
uv run python debug_monitoring_call.py 2>&1 | grep "Request URL"
```
Should show `/monitoring/` in the URL, not `/catalog/`

3. **Check MCP execution:**
Enable DEBUG logging and verify:
- `Endpoint requires authentication: monitoring_get_records` ✓
- `Request URL: .../monitoring/datasets/...` ✓
- `Status Code: 200` ✓

**Note:** After applying this fix, Claude Code must be restarted for the MCP server to reload the updated code.

### Enhanced Tool Descriptions (Jan 2026)

**Problem:** MCP clients (like Claude) didn't have clear guidance on when to use monitoring tools vs catalog tools, leading to errors like calling `ods_get_records` with monitoring datasets.

**Solution:** Enhanced tool descriptions to include explicit usage guidance:

```
[MONITORING API] Perform a query on dataset records.

Use this tool for monitoring datasets (ods-api-monitoring, ods-datasets-monitoring).
For public datasets, use the corresponding catalog tool without 'monitoring' in the name.
This endpoint requires API key authentication.

Endpoint: GET /monitoring/datasets/{dataset_id}/records
```

**Benefits:**
1. Clear indication of which datasets require monitoring tools
2. Explicit guidance to use catalog tools for public datasets
3. Authentication requirements stated upfront
4. Reduces tool selection errors by MCP clients

**Implementation:**
Updated `ods_monitoring_generator.py:145-152` to append usage guidance to all monitoring tool descriptions.

## Design Rationale

### Why Clone Instead of Manual Definition?

**Advantages:**
1. **Automatic updates**: When catalog API changes, monitoring endpoints update automatically
2. **Consistency**: Same parameter structure, validation, documentation
3. **Maintainability**: Single source of truth (OpenAPI spec)
4. **Completeness**: All catalog operations automatically available for monitoring

**Alternatives considered:**
- **Manual endpoint definitions**: Too brittle, requires maintenance
- **Separate OpenAPI spec**: Duplication, version sync issues
- **Runtime path rewriting**: Complex, error-prone

### Why Conditional Auth Instead of Separate Servers?

**Advantages:**
1. **Single MCP server**: Simpler configuration for users
2. **Unified tool namespace**: All ODS tools in one place
3. **Shared infrastructure**: Same executor, registry, error handling
4. **Smart auth**: Automatically applies correct authentication

**Alternatives considered:**
- **Two separate MCP servers**: User confusion, duplicate configuration
- **All endpoints require auth**: Breaks public dataset access
- **No auth ever**: Can't access monitoring datasets

## Future Enhancements

Potential improvements:

1. **Dynamic dataset discovery**: Auto-detect monitoring datasets from API
2. **Permission-based filtering**: Only show monitoring tools if API key has permission
3. **Rate limit handling**: Special handling for monitoring endpoint quotas
4. **Caching**: Cache monitoring data to reduce API calls
5. **Aggregation tools**: Higher-level analytics tools built on monitoring data

## Related Documentation

- [ODS_README.md](./ODS_README.md) - Main ODS MCP server documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Overall adapter architecture
- [LIBRARY_USAGE.md](./LIBRARY_USAGE.md) - Advanced usage patterns
- [tests/test_ods_conditional_auth.py](./tests/test_ods_conditional_auth.py) - Auth tests
- [tests/test_ods_monitoring_generator.py](./tests/test_ods_monitoring_generator.py) - Generator tests

## API Reference

### Class: `ODSMonitoringGenerator`

**Location:** `ods_monitoring_generator.py`

#### Methods

##### `__init__()`
Initialize the monitoring endpoint generator.

```python
generator = ODSMonitoringGenerator()
```

##### `generate_monitoring_endpoints(catalog_endpoints: List[CanonicalEndpoint]) -> List[CanonicalEndpoint]`
Generate monitoring endpoints from catalog endpoints.

**Parameters:**
- `catalog_endpoints`: List of catalog endpoints to clone

**Returns:**
- List of monitoring endpoints with modified paths and security

**Example:**
```python
monitoring_endpoints = generator.generate_monitoring_endpoints(catalog_endpoints)
print(f"Generated {len(monitoring_endpoints)} monitoring endpoints")
```

### Class: `ODSAuthResolver`

**Location:** `ods_auth_resolver.py`

#### Constants

##### `AUTH_REQUIRED_DATASETS`
Set of dataset IDs that require authentication:
- `ods-api-monitoring`
- `ods-datasets-monitoring`

##### `AUTH_REQUIRED_KEYWORDS`
Set of keywords in tool names that suggest auth is needed:
- `monitoring`
- `analytics`

#### Methods

##### `__init__(api_key: Optional[str] = None)`
Initialize the auth resolver.

**Parameters:**
- `api_key`: API key for authenticated requests (default: from `ODS_API_KEY` env var)

##### `resolve_auth(tool_name: str, arguments: Dict[str, Any]) -> AuthHandler`
Determine which auth handler to use.

**Parameters:**
- `tool_name`: Name of the tool being called
- `arguments`: Tool arguments

**Returns:**
- `APIKeyAuth` if authentication required, `NoAuth` otherwise

##### `has_api_key() -> bool`
Check if API key is configured.

**Returns:**
- `True` if API key available, `False` otherwise

### Class: `ODSExecutionHandler`

**Location:** `ods_execution_handler.py`

#### Methods

##### `__init__(tool_provider, executor, endpoints, auth_resolver: ODSAuthResolver)`
Initialize the execution handler with conditional auth.

**Parameters:**
- `tool_provider`: ToolProvider for tool lookup
- `executor`: APIExecutor for making API calls
- `endpoints`: List of CanonicalEndpoint objects
- `auth_resolver`: ODSAuthResolver for auth decisions

##### `execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]`
Execute a tool with conditional authentication.

**Parameters:**
- `tool_name`: Name of tool to execute
- `arguments`: Tool parameter values

**Returns:**
- Execution result in MCP format

## License

This implementation follows the same license as the parent project (REST-to-MCP Adapter).

## Contributing

When modifying monitoring functionality:

1. Update tests in `tests/test_ods_monitoring_generator.py`
2. Add integration tests to `tests/test_ods_conditional_auth.py`
3. Update this documentation
4. Verify server startup with monitoring endpoints enabled
5. Test both authenticated and unauthenticated scenarios

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review server logs with `LOG_LEVEL=DEBUG`
3. Run test suite to verify functionality
4. Open an issue in the repository with logs and reproduction steps
