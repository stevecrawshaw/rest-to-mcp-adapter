#!/usr/bin/env python3
"""
Run Binance MCP Server

This script loads a pre-generated Binance registry and starts the MCP server.

Usage:
    1. First generate the registry:
       python generate_binance_registry.py

    2. Then run the server:
       python run_binance_server.py
"""

import json
import logging
from pathlib import Path

from adapter import (
    MCPServer,
    ToolRegistry,
    APIExecutor,
    NoAuth,
    CanonicalEndpoint,
)
from adapter.mcp import MCPTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_registry_from_file(registry_file: str) -> ToolRegistry:
    """
    Load a pre-generated registry from JSON file.

    Args:
        registry_file: Path to the registry JSON file

    Returns:
        Loaded ToolRegistry
    """
    logger.info(f"Loading registry from {registry_file}...")

    with open(registry_file, 'r') as f:
        data = json.load(f)

    # Create registry
    registry = ToolRegistry(name=data.get('name', 'Binance API'))

    # Load tools
    for tool_data in data.get('tools', []):
        tool = MCPTool(
            name=tool_data['name'],
            description=tool_data['description'],
            inputSchema=tool_data['inputSchema'],
            metadata=tool_data.get('metadata')
        )
        registry.add_tool(tool)

    logger.info(f"✓ Loaded {registry.count()} tools from registry")
    return registry


def load_endpoints_from_file(endpoints_file: str) -> list:
    """
    Load pre-generated endpoints from JSON file.

    Args:
        endpoints_file: Path to the endpoints JSON file

    Returns:
        List of CanonicalEndpoint objects
    """
    logger.info(f"Loading endpoints from {endpoints_file}...")

    with open(endpoints_file, 'r') as f:
        data = json.load(f)

    endpoints = []
    for ep_data in data:
        # Reconstruct CanonicalEndpoint from dict
        endpoint = CanonicalEndpoint(
            path=ep_data['path'],
            method=ep_data['method'],
            operation_id=ep_data.get('operation_id'),
            summary=ep_data.get('summary'),
            description=ep_data.get('description'),
            parameters=ep_data.get('parameters', []),
            request_body=ep_data.get('request_body'),
            responses=ep_data.get('responses', {}),
            tags=ep_data.get('tags', []),
            security=ep_data.get('security', []),
        )
        endpoints.append(endpoint)

    logger.info(f"✓ Loaded {len(endpoints)} endpoints")
    return endpoints


def main():
    """Main function to run the Binance MCP server."""

    # Configuration
    REGISTRY_FILE = "binance_registry.json"
    ENDPOINTS_FILE = "binance_endpoints.json"
    BASE_URL = "https://api.binance.com"

    # Check if files exist
    if not Path(REGISTRY_FILE).exists():
        logger.error(f"Registry file not found: {REGISTRY_FILE}")
        logger.info("Please run: python generate_binance_registry.py")
        return

    if not Path(ENDPOINTS_FILE).exists():
        logger.error(f"Endpoints file not found: {ENDPOINTS_FILE}")
        logger.info("Please run: python generate_binance_registry.py")
        return

    # Load registry and endpoints
    registry = load_registry_from_file(REGISTRY_FILE)
    endpoints = load_endpoints_from_file(ENDPOINTS_FILE)

    # Create executor (Binance public API - no auth for public endpoints)
    # For authenticated endpoints, you would use:
    # from adapter import APIKeyAuth
    # auth = APIKeyAuth(api_key="your_api_key", header_name="X-MBX-APIKEY")
    executor = APIExecutor(
        base_url=BASE_URL,
        auth=NoAuth()
    )

    logger.info(f"Using base URL: {BASE_URL}")
    logger.info("Note: For authenticated endpoints, update the auth configuration")

    # Create MCP server
    server = MCPServer(
        name="Binance Spot API",
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("=" * 70)
    logger.info(f"Starting {server.name} v{server.version}")
    logger.info(f"Tools: {registry.count()}")
    logger.info(f"Endpoints: {len(endpoints)}")
    logger.info("=" * 70)

    # Run the server
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
