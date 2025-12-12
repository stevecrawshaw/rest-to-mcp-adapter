#!/usr/bin/env python3
"""
OpenDataSoft MCP Server for West of England Combined Authority

This MCP server provides Claude Code with access to the West of England
OpenDataSoft API, enabling queries on public datasets about transportation,
demographics, planning, and more.

Configuration via environment variables:
- ODS_BASE_URL: Base URL for the ODS API (default: https://opendata.westofengland-ca.gov.uk/api/explore/v2.1)
- ODS_OPENAPI_URL: OpenAPI spec URL (default: {BASE_URL}/swagger.json)
- ODS_SERVER_NAME: MCP server name (default: "West of England OpenDataSoft")
- ODS_SERVER_VERSION: Server version (default: "1.0.0")
- LOG_LEVEL: Logging level (default: "INFO")

Usage:
    python ods_server.py

For Claude Code configuration, see ODS_README.md
"""

import os
import sys
import logging
from typing import Optional

from adapter import (
    ToolRegistry,
    MCPServer,
    APIExecutor,
    NoAuth,
)


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the ODS server."""
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
    """
    return {
        'base_url': os.getenv(
            'ODS_BASE_URL',
            'https://opendata.westofengland-ca.gov.uk/api/explore/v2.1'
        ),
        'openapi_url': os.getenv(
            'ODS_OPENAPI_URL',
            'https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json'
        ),
        'server_name': os.getenv(
            'ODS_SERVER_NAME',
            'West of England OpenDataSoft'
        ),
        'server_version': os.getenv(
            'ODS_SERVER_VERSION',
            '1.0.0'
        ),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    }


def create_ods_server(config: dict) -> MCPServer:
    """
    Create and configure the ODS MCP server.

    Args:
        config: Configuration dictionary

    Returns:
        Configured MCPServer instance

    Raises:
        Exception: If server creation fails
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Loading OpenAPI spec from: {config['openapi_url']}")

        # Phase 1-3: Load OpenAPI → Normalize → Generate MCP tools
        # Using the convenience method that combines all phases
        registry = ToolRegistry.create_from_openapi(
            source=config['openapi_url'],
            name=config['server_name'],
            api_name="ods",  # Prefix for tool names
            auto_detect_auth=True,  # Auto-detect auth parameters (should find none for public API)
            include_metadata=True,  # Include HTTP method, path, tags, etc.
        )

        logger.info(f"Created registry with {registry.count()} tools")

        # Log first few tool names for verification
        tool_names = registry.get_tool_names()
        if tool_names:
            preview = ', '.join(tool_names[:5])
            logger.info(f"Sample tools: {preview}{'...' if len(tool_names) > 5 else ''}")

        # Phase 4: Set up executor with NoAuth (public API)
        executor = APIExecutor(
            base_url=config['base_url'],
            auth=NoAuth(),  # Public API - no authentication required
            timeout=30,  # 30 second timeout
            max_retries=3,  # Retry failed requests up to 3 times
        )

        logger.info("Created executor with NoAuth (public API)")

        # Create MCP server - endpoints are automatically included in registry
        server = MCPServer(
            name=config['server_name'],
            version=config['server_version'],
            tool_registry=registry,
            executor=executor,
        )

        logger.info(f"MCP Server '{config['server_name']}' v{config['server_version']} ready")
        return server

    except Exception as e:
        logger.error(f"Failed to create ODS server: {e}", exc_info=True)
        raise


def main():
    """Main entry point for the ODS MCP server."""
    # Load configuration
    config = get_env_config()

    # Setup logging
    setup_logging(config['log_level'])
    logger = logging.getLogger(__name__)

    logger.info("Starting West of England OpenDataSoft MCP Server")
    logger.info(f"Base URL: {config['base_url']}")

    try:
        # Create server
        server = create_ods_server(config)

        # Run server (blocks until stopped)
        logger.info("Server starting on stdio transport...")
        server.run()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
