#!/usr/bin/env python3
"""
Energy Performance Certificates (EPC) MCP Server

This MCP server provides Claude Code with access to the UK Energy Performance
Certificates API, enabling queries on domestic and non-domestic building
energy ratings, certificates, and recommendations.

Configuration via environment variables:
- EPC_BASE_URL: Base URL for the EPC API (default: https://epc.opendatacommunities.org)
- EPC_OPENAPI_PATH: Path to OpenAPI spec file (default: epc.yml)
- EPC_USERNAME: Email address for API authentication (REQUIRED)
- EPC_PASSWORD: API key for authentication (REQUIRED)
- EPC_SERVER_NAME: MCP server name (default: "UK Energy Performance Certificates")
- EPC_SERVER_VERSION: Server version (default: "1.0.0")
- LOG_LEVEL: Logging level (default: "INFO")

Usage:
    python epc_server.py

The EPC API uses HTTP Basic Authentication where:
- Username: Your registered email address
- Password: Your API key

For Claude Code configuration, add to MCP settings:
    claude mcp add epc-certificates "uv run --directory <path-to-repo> epc_server.py"
"""

import os
import sys
import logging
from typing import Optional

from adapter import (
    ToolRegistry,
    MCPServer,
    APIExecutor,
    BasicAuth,
)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the EPC server."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # Log to stderr to not interfere with stdio transport
        ]
    )


def get_env_config() -> dict:
    """
    Load configuration from environment variables with sensible defaults.

    Returns:
        dict: Configuration dictionary

    Note:
        EPC_USERNAME and EPC_PASSWORD are required and must be set.
    """
    return {
        'base_url': os.getenv(
            'EPC_BASE_URL',
            'https://epc.opendatacommunities.org'
        ),
        'openapi_path': os.getenv(
            'EPC_OPENAPI_PATH',
            'epc.yml'
        ),
        'username': os.getenv('EPC_USERNAME'),  # Required
        'password': os.getenv('EPC_PASSWORD'),  # Required
        'server_name': os.getenv(
            'EPC_SERVER_NAME',
            'UK Energy Performance Certificates'
        ),
        'server_version': os.getenv(
            'EPC_SERVER_VERSION',
            '1.0.0'
        ),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    }


def create_epc_server(config: dict) -> MCPServer:
    """
    Create and configure the EPC MCP server.

    Args:
        config: Configuration dictionary

    Returns:
        Configured MCPServer instance

    Raises:
        ValueError: If required credentials are missing
        Exception: If server creation fails
    """
    logger = logging.getLogger(__name__)

    # Validate required credentials
    if not config.get('username') or not config.get('password'):
        raise ValueError(
            "EPC_USERNAME and EPC_PASSWORD environment variables must be set. "
            "These are your registered email address and API key from "
            "https://epc.opendatacommunities.org"
        )

    try:
        logger.info(f"Loading OpenAPI spec from: {config['openapi_path']}")

        # Phase 1-3: Load OpenAPI → Normalize → Generate MCP tools
        # Using the convenience method that combines all phases
        registry = ToolRegistry.create_from_openapi(
            source=config['openapi_path'],  # Local file path
            name=config['server_name'],
            api_name="epc",  # Prefix for tool names
            auto_detect_auth=True,  # Auto-detect auth parameters from spec
            include_metadata=True,  # Include HTTP method, path, tags, etc.
        )

        logger.info(f"Created registry with {registry.count()} tools")

        # Log first few tool names for verification
        tool_names = registry.get_tool_names()
        if tool_names:
            preview = ', '.join(tool_names[:5])
            logger.info(f"Sample tools: {preview}{'...' if len(tool_names) > 5 else ''}")

        # Phase 4: Set up executor with BasicAuth
        # Note: The epc.yml has a relative server URL (/api/v1)
        # We override it here with the full base URL + path
        executor = APIExecutor(
            base_url=config['base_url'] + '/api/v1',  # Full URL with API path
            auth=BasicAuth(
                username=config['username'],
                password=config['password']
            ),
            timeout=30,  # 30 second timeout
            max_retries=3,  # Retry failed requests up to 3 times
        )

        logger.info(f"Created executor with BasicAuth (username='{config['username']}')")

        # Create MCP server - endpoints are automatically included in registry
        server = MCPServer(
            name=config['server_name'],
            version=config['server_version'],
            tool_registry=registry,
            executor=executor,
        )

        logger.info(f"MCP Server '{config['server_name']}' v{config['server_version']} ready")
        return server

    except FileNotFoundError as e:
        logger.error(f"OpenAPI spec file not found: {config['openapi_path']}")
        logger.error("Please ensure epc.yml is in the project root directory")
        raise
    except Exception as e:
        logger.error(f"Failed to create EPC server: {e}", exc_info=True)
        raise


def main():
    """Main entry point for the EPC MCP server."""
    # Load configuration
    config = get_env_config()

    # Setup logging
    setup_logging(config['log_level'])
    logger = logging.getLogger(__name__)

    logger.info("Starting UK Energy Performance Certificates MCP Server")
    logger.info(f"Base URL: {config['base_url']}")

    try:
        # Create server
        server = create_epc_server(config)

        # Run server (blocks until stopped)
        logger.info("Server starting on stdio transport...")
        server.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except ValueError as e:
        # Configuration error (missing credentials)
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
