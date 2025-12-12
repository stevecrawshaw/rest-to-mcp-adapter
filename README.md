# West of England OpenDataSoft MCP Server

This MCP server provides Claude with access to the West of England Combined Authority's OpenDataSoft API, enabling exploration of public datasets including transportation, demographics, planning, and regional statistics. It was created using the code in this [repo](https://github.com/pawneetdev/rest-to-mcp-adapter).

## Features

- **Public API**: No authentication required
- **Auto-generated Tools**: Automatically generates MCP tools from OpenAPI specification
- **Complete Coverage**: Access to all OpenDataSoft v2.1 API endpoints
- **Robust Execution**: Built-in retry logic and error handling
- **Configurable**: Environment variable-based configuration with sensible defaults

## Quick Start

### 1. Prerequisites

- **uv** package manager installed ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Claude Code CLI** installed ([installation guide](https://github.com/anthropics/claude-code))

### 2. Test the Server

Run the server directly to verify it works:

```bash
cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
uv run ods_server.py
```

The server will start and wait for JSON-RPC messages on stdin. You should see log output like:

```
2024-01-15 10:30:00 - __main__ - INFO - Starting West of England OpenDataSoft MCP Server
2024-01-15 10:30:00 - __main__ - INFO - Base URL: https://opendata.westofengland-ca.gov.uk/api/explore/v2.1
2024-01-15 10:30:01 - __main__ - INFO - Loading OpenAPI spec from: https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json
2024-01-15 10:30:02 - __main__ - INFO - Created registry with 12 tools
2024-01-15 10:30:02 - __main__ - INFO - Sample tools: ods_get_datasets, ods_get_dataset, ods_get_records...
2024-01-15 10:30:02 - __main__ - INFO - MCP Server 'West of England OpenDataSoft' v1.0.0 ready
2024-01-15 10:30:02 - __main__ - INFO - Server starting on stdio transport...
```

Press Ctrl+C to stop.

### 3. Configure Claude Code

Add the MCP server using the Claude Code CLI:

```bash
claude mcp add west-england-ods "uv run --directory C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter ods_server.py"
```

Or manually add to Claude Code config (typically `~/.claude.json`):

```json
{
  "mcpServers": {
    "west-england-ods": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter",
        "ods_server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**For Claude Desktop** (legacy, use Claude Code CLI instead):

```json
{
  "mcpServers": {
    "west-england-ods": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/rest-to-mcp-adapter",
        "ods_server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 4. Verify Connection

Check the server status:

```bash
claude mcp list
```

You should see `west-england-ods` with a ✓ Connected status.

### 5. Test in Claude Code

Ask Claude:

```
"What datasets are available in OpenDataSoft?"
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ODS_BASE_URL` | Base URL for API | `https://opendata.westofengland-ca.gov.uk/api/explore/v2.1` |
| `ODS_OPENAPI_URL` | OpenAPI spec URL | `{BASE_URL}/swagger.json` |
| `ODS_SERVER_NAME` | Server name | `West of England OpenDataSoft` |
| `ODS_SERVER_VERSION` | Server version | `1.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Using a .env File (Optional)

If you want to use a `.env` file instead of passing environment variables through Claude Desktop:

1. Copy the example:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferences

3. Install python-dotenv:

   ```bash
   pip install python-dotenv
   ```

4. Modify `ods_server.py` to load the .env file (add at the top of `main()`):

   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Configuration via Claude Desktop (Recommended)

Pass environment variables directly in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "west-england-ods": {
      "command": "python",
      "args": ["C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter/ods_server.py"],
      "env": {
        "ODS_BASE_URL": "https://opendata.westofengland-ca.gov.uk/api/explore/v2.1",
        "ODS_SERVER_NAME": "West England Data",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Available Tools

The server automatically generates tools for all OpenDataSoft API endpoints. Key tools include:

### Catalog Tools

- **mcp__west-england-ods__ods_get_datasets** - List all available datasets (121 total)
- **mcp__west-england-ods__ods_get_dataset** - Get metadata for a specific dataset
- **mcp__west-england-ods__ods_get_datasets_facets** - Enumerate facet values across datasets
- **mcp__west-england-ods__ods_list_export_formats** - List available export formats
- **mcp__west-england-ods__ods_export_datasets** - Export catalog in various formats

### Dataset Tools

- **mcp__west-england-ods__ods_get_records** - Query records from a dataset
- **mcp__west-england-ods__ods_get_record** - Retrieve a single record by ID
- **mcp__west-england-ods__ods_get_records_facets** - Enumerate facet values for dataset records
- **mcp__west-england-ods__ods_list_dataset_export_formats** - List export formats for a dataset
- **mcp__west-england-ods__ods_export_records** - Export dataset records
- **mcp__west-england-ods__ods_get_dataset_attachments** - Get dataset attachments

### Export Tools

- **mcp__west-england-ods__ods_export_catalog_csv** - Export catalog as CSV
- **mcp__west-england-ods__ods_export_catalog_dcat** - Export as RDF/XML with DCAT
- **mcp__west-england-ods__ods_export_records_csv** - Export records as CSV
- **mcp__west-england-ods__ods_export_records_parquet** - Export records as Parquet
- **mcp__west-england-ods__ods_export_records_gpx** - Export records as GPX

All tools follow the naming convention: `mcp__west-england-ods__<operation_name>`

## Available Datasets

The West of England Combined Authority hosts **121 datasets** covering:

### Featured Datasets

**Energy & Environment**

- `lep-epc-domestic-point` - Energy Performance Certificates (372,078 properties)
- `lc_gordano_gen_data` - Low Carbon Energy Generation
- `wards_solar_install_visits_v4` - Solar Together Installations
- `swnzh-cef-projects` - Community Energy Fund Projects

**Nature & Ecology**

- `ods-os-open-rivers` - Rivers and watercourses (849 features)
- `lnrs-areas-important` - Areas of Importance to Biodiversity (1,111 sites)
- `roadkill-lep-st` - Roadkill observations (833 records)
- `mapped-river-floodplain-measures-precise` - River floodplain restoration measures

**Demographics & Census**

- `ethnicity_lep_lsoa` - Ethnicity by LSOA (2021 census)
- `census-2021-dwelling-stock-per-hectare` - Dwelling density by LSOA

**Education & Skills**

- `weca-apprenticeship-starts` - Apprenticeship starts (24,925 records)

**Geography**

- `lep-boundary` - West of England LEP boundary
- `lsoa-ward-lsoa-lookup-lep` - Geographic lookup tables

To discover more datasets:

```
"List all datasets with the theme 'Environment'"
```

## User Guide

### Understanding Tool Names

All MCP tools are prefixed with the server name to avoid conflicts:

- **Pattern**: `mcp__<server-name>__<operation>`
- **Example**: `mcp__west-england-ods__ods_get_datasets`

You don't need to use the full name when asking Claude - just describe what you want naturally.

### Common Workflows

#### 1. Discovering Datasets

**List all datasets**:

```
"What datasets are available in OpenDataSoft?"
```

**Find datasets by theme**:

```
"Show me all Environment-themed datasets"
```

**Search for specific topics**:

```
"Find datasets about energy performance or solar panels"
```

#### 2. Exploring Dataset Details

**Get metadata for a dataset**:

```
"What is the metadata for the domestic EPC dataset?"
```

**Check record count**:

```
"How many records are in the lep-epc-domestic-point dataset?"
```

**Understand dataset fields**:

```
"What fields are available in the apprenticeship starts dataset?"
```

#### 3. Querying Records

**Get sample records**:

```
"Get 10 records from the rivers dataset"
```

**Filter by field**:

```
"Get EPC records where current_energy_rating is 'A'"
```

**Use ODSQL where clauses**:

```
"Query the EPC dataset where total_floor_area > 100 and current_energy_rating in ('A', 'B')"
```

**Order results**:

```
"Get apprenticeship starts ordered by start_date descending, limit 20"
```

#### 4. Working with Geographic Data

**Find geographic datasets**:

```
"Which datasets have geographic data (geo_point_2d or geo_shape)?"
```

**Query by location**:

```
"Get biodiversity sites within Bristol"
```

#### 5. Aggregating Data

**Group by facets**:

```
"Group EPC records by current_energy_rating and count them"
```

**Get facet values**:

```
"What are the available energy ratings in the EPC dataset?"
```

### Query Parameters

The OpenDataSoft API supports various query parameters:

**Filtering**:

- `where` - ODSQL query expression (e.g., `"age > 18 AND city='Bristol'"`)
- `refine` - Facet refinement (e.g., `"theme:Environment"`)
- `exclude` - Exclude facet values

**Pagination**:

- `limit` - Number of results (default: 10, max: 100 for records)
- `offset` - Starting position

**Selection**:

- `select` - Fields to return (e.g., `"dataset_id, metas.default.title"`)

**Ordering**:

- `order_by` - Sort expression (e.g., `"start_date desc"`)

**Examples**:

```
"Get 50 EPC records with limit=50 and select only property_type and current_energy_rating fields"
```

```
"Query apprenticeships where apps_level='Advanced' with offset=0 and limit=100"
```

## Usage Examples

### Example 1: Energy Analysis

**Query**: "Analyze the distribution of EPC ratings in the domestic properties dataset"

Claude will:

1. Use `ods_get_dataset` to understand the schema
2. Use `ods_get_records_facets` to get rating distributions
3. Present summary statistics

### Example 2: Geographic Exploration

**Query**: "Show me all rivers in the dataset and count them by form (canal, stream, etc.)"

Claude will:

1. Use `ods_get_records` from `ods-os-open-rivers`
2. Group by the `form` field
3. Present counts and examples

### Example 3: Time Series Data

**Query**: "Show me apprenticeship starts by month for the last year"

Claude will:

1. Query `weca-apprenticeship-starts` dataset
2. Filter by date range using `where` clause
3. Aggregate by month using `group_by`
4. Present trends

### Example 4: Complex Query

**Query**: "Find all domestic properties with solar panels (photo_supply > 0) that have an energy rating below C, located in Bristol"

Claude will:

1. Query `lep-epc-domestic-point`
2. Apply multiple filters in `where` clause
3. Return matching records with relevant fields

### Example 5: Export Data

**Query**: "Export the first 1000 EPC records as CSV"

Claude will:

1. Use `ods_export_records_csv`
2. Set `limit=1000` and `dataset_id=lep-epc-domestic-point`
3. Return the CSV data or download link

## Portability & Design Learnings

### Why `uv run --directory`?

The current configuration uses `uv run --directory` instead of a hardcoded `.venv` path. This approach offers several advantages:

**Previous approach (not recommended)**:

```bash
# Required hardcoded path to .venv
C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter/.venv/Scripts/python.exe ods_server.py
```

**Current approach (recommended)**:

```bash
# Uses uv with project context
uv run --directory C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter ods_server.py
```

**Benefits**:

1. ✅ **No .venv dependency**: Works even if you delete/recreate the virtual environment
2. ✅ **Automatic dependency resolution**: uv reads `pyproject.toml` automatically
3. ✅ **More portable**: Easier to share or move the project
4. ✅ **Cleaner config**: No need to manage Python interpreter paths
5. ✅ **Project-aware**: Automatically uses the `adapter` module from the project context

### Future: Inline Dependencies with PEP 723

Once `rest-to-mcp-adapter` is published to PyPI, the server could use inline script metadata for complete portability:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#     "rest-to-mcp-adapter>=0.2.0b1",
# ]
# ///
```

Then the config would simply be:

```bash
uv run ods_server.py  # No --directory needed!
```

This would make the script fully self-contained and runnable from anywhere.

### Project Structure Notes

The server relies on:

- **`adapter/` module** - Core library from this project
- **`pyproject.toml`** - Dependencies and project metadata
- **`ods_server.py`** - MCP server implementation

Using `uv run --directory` ensures all three are correctly resolved without manual path management.

## Troubleshooting

### Server Not Connecting

1. **Check server status**:

   ```bash
   claude mcp list
   ```

   Look for `west-england-ods` with ✓ Connected status.

2. **Verify uv is installed**:

   ```bash
   uv --version
   ```

   If not installed, see: <https://docs.astral.sh/uv/getting-started/installation/>

3. **Test server manually**:

   ```bash
   cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
   uv run ods_server.py
   ```

   Server should start and show log output. Press Ctrl+C to stop.

4. **Check project dependencies**:

   ```bash
   cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
   uv sync
   ```

5. **Verify absolute path**: The `--directory` argument must be an absolute path:
   - ✅ Good: `C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter`
   - ❌ Bad: `./rest-to-mcp-adapter` or `~/projects/rest-to-mcp-adapter`

### Server Starting but No Tools Available

1. **Verify OpenAPI spec is accessible**:

   ```bash
   curl https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json
   ```

2. **Check network connectivity**: Ensure you can reach `opendata.westofengland-ca.gov.uk`

3. **Review server logs**: Look for error messages in stderr output

### Server Crashes on Startup

1. **Sync dependencies**:

   ```bash
   cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
   uv sync
   ```

2. **Verify library can be imported**:

   ```bash
   uv run python -c "from adapter import ToolRegistry, MCPServer, APIExecutor, NoAuth; print('OK')"
   ```

3. **Test with debug logging**:
   Update MCP config to enable debug logs:

   ```bash
   claude mcp remove west-england-ods
   claude mcp add west-england-ods "uv run --directory C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter ods_server.py" --env LOG_LEVEL=DEBUG
   ```

   Or manually edit config:

   ```json
   "env": {
     "LOG_LEVEL": "DEBUG"
   }
   ```

4. **Check uv can find pyproject.toml**:

   ```bash
   ls C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter/pyproject.toml
   ```

### API Calls Failing

1. **Check API availability**: Visit <https://opendata.westofengland-ca.gov.uk> in your browser

2. **Review retry settings**: The server retries failed requests up to 3 times with exponential backoff

3. **Check for rate limiting**: The API may have rate limits (though unlikely for public endpoints)

### Debugging Tips

**Enable debug logging** via MCP config:

```bash
claude mcp remove west-england-ods
claude mcp add west-england-ods "uv run --directory C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter ods_server.py" --env LOG_LEVEL=DEBUG
```

**Run manually to see logs** (Windows):

```bash
set LOG_LEVEL=DEBUG
cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
uv run ods_server.py
```

**Run manually to see logs** (Mac/Linux):

```bash
export LOG_LEVEL=DEBUG
cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
uv run ods_server.py
```

**Test OpenAPI loading**:

```bash
cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
uv run python -c "from adapter import OpenAPILoader; loader = OpenAPILoader(); spec = loader.load('https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json'); print(f'Loaded {len(spec.get(\"paths\", {}))} endpoints')"
```

**Check tool generation**:

```bash
cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
uv run python -c "from adapter import ToolRegistry; registry = ToolRegistry.create_from_openapi('https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json', api_name='ods'); print(f'{registry.count()} tools: {registry.get_tool_names()}')"
```

**View MCP server logs** (if using Claude Desktop):

- Windows: `%APPDATA%\Claude\logs\`
- Mac: `~/Library/Logs/Claude/`

**Check Claude Code status**:

```bash
claude mcp list
claude mcp get west-england-ods
```

## Architecture

This server is built on the `rest-to-mcp-adapter` library and follows a 4-phase pipeline:

1. **Load**: Fetch and parse OpenAPI specification from the ODS API
2. **Normalize**: Convert to canonical endpoint format
3. **Generate**: Create MCP tool definitions with proper JSON schemas
4. **Execute**: Run the MCP server with stdio transport

For more details, see the main project:

- [README.md](README.md) - Library overview and usage
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design decisions and architecture
- [LIBRARY_USAGE.md](LIBRARY_USAGE.md) - Advanced usage patterns

## Extending to Other OpenDataSoft Instances

This server is configured for West of England, but you can easily adapt it for any OpenDataSoft instance:

1. **Create a new server script** (e.g., `ods_custom_server.py`)
2. **Change the default URLs**:

   ```python
   'base_url': os.getenv(
       'ODS_BASE_URL',
       'https://your-custom-instance.opendatasoft.com/api/explore/v2.1'
   ),
   ```

3. **Update the API name** to avoid conflicts:

   ```python
   registry = ToolRegistry.create_from_openapi(
       source=config['openapi_url'],
       api_name="custom_ods",  # Change this prefix
   )
   ```

4. **Add to Claude Desktop config** with a different key

## Performance Notes

- **Startup time**: First load fetches and parses the OpenAPI spec (typically 1-3 seconds)
- **Tool count**: 12 tools for West of England OpenDataSoft API
- **Request timeout**: 30 seconds (configurable in `APIExecutor`)
- **Retry logic**: 3 attempts with exponential backoff
- **Memory usage**: Minimal (~50-100 MB)
- **Response times**: Typical queries complete in 200-500ms

## Quick Reference

### Installation & Setup

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Mac/Linux
# or download from: https://docs.astral.sh/uv/getting-started/installation/

# 2. Add MCP server
claude mcp add west-england-ods "uv run --directory C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter ods_server.py"

# 3. Verify connection
claude mcp list

# 4. Test in Claude Code
# Ask: "What datasets are available in OpenDataSoft?"
```

### Common Commands

```bash
# List MCP servers
claude mcp list

# Get server details
claude mcp get west-england-ods

# Remove server
claude mcp remove west-england-ods

# Test server manually
cd C:/Users/steve.crawshaw/projects/rest-to-mcp-adapter
uv run ods_server.py

# Sync dependencies
uv sync

# Enable debug logging
claude mcp add west-england-ods "uv run --directory C:/path/to/project ods_server.py" --env LOG_LEVEL=DEBUG
```

### Useful Queries

```
"List all available datasets"
"What is the metadata for the domestic EPC dataset?"
"How many records are in lep-epc-domestic-point?"
"Get 10 sample records from the rivers dataset"
"Find all datasets with geographic data"
"Query EPCs where current_energy_rating='A' and limit to 50 results"
"Export the first 1000 apprenticeship records as CSV"
```

### Dataset IDs Reference

| Dataset ID | Description | Records |
|------------|-------------|---------|
| `lep-epc-domestic-point` | Energy Performance Certificates | 372,078 |
| `weca-apprenticeship-starts` | Apprenticeship Starts | 24,925 |
| `lnrs-areas-important` | Biodiversity Areas | 1,111 |
| `ods-os-open-rivers` | Rivers & Watercourses | 849 |
| `roadkill-lep-st` | Roadkill Observations | 833 |
| `ethnicity_lep_lsoa` | Ethnicity by LSOA | 699 |
| `census-2021-dwelling-stock-per-hectare` | Dwelling Density | 699 |

See full list: Ask Claude "List all datasets"

## Support

For issues specific to this ODS server implementation:

- Check this README's troubleshooting section
- Review the main project [README.md](README.md)
- Open an issue on the rest-to-mcp-adapter repository

For questions about the West of England OpenDataSoft API:

- Visit: <https://opendata.westofengland-ca.gov.uk>
- API documentation: <https://opendata.westofengland-ca.gov.uk/api/explore/v2.1>

## License

This server implementation inherits the MIT license from the `rest-to-mcp-adapter` project.

## Related Resources

- **OpenDataSoft Documentation**: <https://help.opendatasoft.com/apis/ods-search-v2/>
- **MCP Protocol**: <https://modelcontextprotocol.io/>
- **Claude Desktop**: <https://claude.ai/download>
