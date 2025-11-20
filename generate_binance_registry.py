#!/usr/bin/env python3
"""
Generate Binance API registry and endpoint files.

This script:
1. Loads the Binance OpenAPI specification
2. Normalizes it to canonical endpoints
3. Generates MCP tools
4. Saves registry and endpoints to JSON files

Usage:
    python generate_binance_registry.py

Output files:
    - binance_registry.json: MCP tool definitions
    - binance_endpoints.json: Canonical endpoint data
"""

import json
import logging
from pathlib import Path

from adapter import OpenAPILoader, Normalizer, ToolGenerator, ToolRegistry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generate Binance registry and endpoint files."""

    # Binance Spot API OpenAPI spec
    BINANCE_SPEC_URL = "https://raw.githubusercontent.com/binance/binance-api-swagger/refs/heads/master/spot_api.yaml"

    logger.info("=" * 70)
    logger.info("Generating Binance API Registry")
    logger.info("=" * 70)

    # Step 1: Load OpenAPI spec
    logger.info(f"\n1. Loading OpenAPI spec from: {BINANCE_SPEC_URL}")
    loader = OpenAPILoader()
    spec = loader.load(BINANCE_SPEC_URL)
    logger.info("✓ OpenAPI spec loaded successfully")

    # Step 2: Normalize endpoints
    logger.info("\n2. Normalizing endpoints...")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"✓ Normalized {len(endpoints)} endpoints")

    # Step 3: Generate MCP tools
    logger.info("\n3. Generating MCP tools...")
    generator = ToolGenerator(api_name="binance", include_metadata=True)
    tools = generator.generate_tools(endpoints)
    logger.info(f"✓ Generated {len(tools)} MCP tools")

    # Step 4: Create registry
    logger.info("\n4. Creating tool registry...")
    registry = ToolRegistry(name="Binance Spot API")
    for tool in tools:
        registry.add_tool(tool)
    logger.info(f"✓ Registry created with {registry.count()} tools")

    # Step 5: Save registry to file
    registry_file = Path("binance_registry.json")
    logger.info(f"\n5. Saving registry to: {registry_file}")

    registry_data = {
        "name": "Binance Spot API",
        "version": "1.0.0",
        "description": "MCP tools for Binance Spot trading API",
        "tools": [tool.to_dict() for tool in tools]
    }

    with open(registry_file, 'w') as f:
        json.dump(registry_data, f, indent=2)
    logger.info(f"✓ Registry saved to {registry_file}")

    # Step 6: Save endpoints to file (for runtime execution)
    endpoints_file = Path("binance_endpoints.json")
    logger.info(f"\n6. Saving endpoints to: {endpoints_file}")

    # Convert endpoints to dict format using model_dump()
    endpoints_data = [ep.model_dump() for ep in endpoints]

    with open(endpoints_file, 'w') as f:
        json.dump(endpoints_data, f, indent=2)
    logger.info(f"✓ Endpoints saved to {endpoints_file}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✓ Registry generation complete!")
    logger.info("=" * 70)
    logger.info(f"Registry file: {registry_file} ({len(tools)} tools)")
    logger.info(f"Endpoints file: {endpoints_file} ({len(endpoints)} endpoints)")
    logger.info("\nNext steps:")
    logger.info("  1. Set up credentials:")
    logger.info("     cp binance_config.json.example binance_config.json")
    logger.info("     # Edit binance_config.json with your API key and secret")
    logger.info("  2. Run the server:")
    logger.info("     python run_binance_server.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Error generating registry: {e}", exc_info=True)
