#!/usr/bin/env python3
"""
Test script to verify authentication parameters are filtered out.
"""

from adapter import OpenAPILoader, Normalizer, ToolGenerator

# Load Binance spec
print("Loading Binance OpenAPI spec...")
loader = OpenAPILoader()
spec = loader.load("https://raw.githubusercontent.com/binance/binance-api-swagger/refs/heads/master/spot_api.yaml")

# Normalize
print("Normalizing endpoints...")
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Find an authenticated endpoint (e.g., GET /api/v3/account)
account_endpoint = None
for ep in endpoints:
    if ep.path == "/api/v3/account" and ep.method == "GET":
        account_endpoint = ep
        break

if not account_endpoint:
    print("ERROR: Could not find GET /api/v3/account endpoint")
    exit(1)

print(f"\nFound endpoint: {account_endpoint.method} {account_endpoint.path}")
print(f"Total parameters: {len(account_endpoint.parameters)}")
print("Parameters:")
for param in account_endpoint.parameters:
    print(f"  - {param.name} ({param.location})")

# Generate tool
print("\nGenerating MCP tool...")
generator = ToolGenerator(api_name="binance")
tool = generator.generate_tool(account_endpoint)

print(f"\nGenerated tool: {tool.name}")
print(f"Input schema properties:")
for prop_name in tool.inputSchema.get("properties", {}).keys():
    print(f"  - {prop_name}")

# Check if auth params are present
auth_params = ['signature', 'timestamp', 'recvWindow', 'recv_window']
found_auth_params = [p for p in auth_params if p in tool.inputSchema.get("properties", {})]

if found_auth_params:
    print(f"\n❌ ERROR: Auth parameters found in schema: {found_auth_params}")
    print("These should be filtered out!")
    exit(1)
else:
    print("\n✓ SUCCESS: No auth parameters in schema")
    print("Auth parameters will be added automatically by BinanceAuth handler")
