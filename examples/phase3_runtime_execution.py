"""
Phase 3: Runtime Execution Engine Examples

This file demonstrates how to use the runtime execution engine to make
actual REST API calls using canonical endpoints.

Examples:
1. Basic API execution with no authentication
2. API execution with Bearer token authentication
3. API execution with API key authentication
4. Handling different parameter locations
5. Error handling and retries
6. Complete workflow: Load → Normalize → Generate → Execute
"""

from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.mcp import ToolGenerator, ToolRegistry
from adapter.runtime import (
    APIExecutor,
    NoAuth,
    APIKeyAuth,
    BearerAuth,
    BasicAuth,
    RequestBuilder,
)


def example1_basic_execution():
    """
    Example 1: Basic API execution with no authentication.

    Demonstrates executing a simple GET request to a public API.
    """
    print("\n" + "=" * 70)
    print("Example 1: Basic API Execution (No Auth)")
    print("=" * 70)

    # Create a simple endpoint manually for demonstration
    from adapter.parsing.canonical_models import (
        CanonicalEndpoint,
        CanonicalParameter,
        DataType,
        ParameterLocation,
    )

    # Define endpoint: GET /users/{user_id}
    endpoint = CanonicalEndpoint(
        name="get_user_by_id",
        path="/users/{user_id}",
        method="GET",
        description="Retrieve user information by ID",
        parameters=[
            CanonicalParameter(
                name="user_id",
                location=ParameterLocation.PATH,
                type=DataType.STRING,
                required=True,
                description="The user ID",
            )
        ],
    )

    # Create executor (using JSONPlaceholder as example API)
    executor = APIExecutor(
        base_url="https://jsonplaceholder.typicode.com",
        auth=NoAuth(),
    )

    # Execute the API call
    result = executor.execute(
        endpoint=endpoint,
        parameters={"user_id": "1"},
    )

    # Display results
    print(f"\n✓ Endpoint: {result.endpoint_name}")
    print(f"✓ Success: {result.success}")
    print(f"✓ Status Code: {result.response.status_code}")
    print(f"✓ Execution Time: {result.execution_time_ms:.2f}ms")
    print(f"✓ Attempts: {result.attempts}")

    if result.success:
        print(f"\n✓ Response Data:")
        import json

        print(json.dumps(result.response.data, indent=2))
    else:
        print(f"\n✗ Error: {result.response.error}")


def example2_bearer_auth():
    """
    Example 2: API execution with Bearer token authentication.

    Demonstrates using Bearer token for authenticated requests.
    """
    print("\n" + "=" * 70)
    print("Example 2: Bearer Token Authentication")
    print("=" * 70)

    from adapter.parsing.canonical_models import (
        CanonicalEndpoint,
        CanonicalParameter,
        DataType,
        ParameterLocation,
    )

    # Define endpoint
    endpoint = CanonicalEndpoint(
        name="list_repos",
        path="/user/repos",
        method="GET",
        description="List authenticated user's repositories",
        parameters=[
            CanonicalParameter(
                name="type",
                location=ParameterLocation.QUERY,
                type=DataType.STRING,
                required=False,
                description="Repository type filter",
            )
        ],
    )

    # Note: This example won't actually work without a valid GitHub token
    # It demonstrates the API, not a real call
    auth = BearerAuth(token="ghp_your_token_here")

    executor = APIExecutor(
        base_url="https://api.github.com",
        auth=auth,
    )

    print(f"\n✓ Executor created with Bearer authentication")
    print(f"✓ Base URL: https://api.github.com")
    print(f"✓ Endpoint: {endpoint.name} ({endpoint.method} {endpoint.path})")
    print(
        "\nNote: This example requires a valid GitHub token to execute."
        "\nReplace 'ghp_your_token_here' with an actual token to test."
    )


def example3_api_key_auth():
    """
    Example 3: API execution with API key authentication.

    Demonstrates different API key locations (header, query parameter).
    """
    print("\n" + "=" * 70)
    print("Example 3: API Key Authentication")
    print("=" * 70)

    from adapter.parsing.canonical_models import (
        CanonicalEndpoint,
        DataType,
        ParameterLocation,
    )

    endpoint = CanonicalEndpoint(
        name="get_weather",
        path="/current",
        method="GET",
        description="Get current weather",
        parameters=[],
    )

    # API key in header
    print("\n→ API Key in Header:")
    auth_header = APIKeyAuth(
        key="your-api-key",
        location="header",
        name="X-API-Key",
    )
    print(f"  {auth_header}")

    # API key in query parameter
    print("\n→ API Key in Query Parameter:")
    auth_query = APIKeyAuth(
        key="your-api-key",
        location="query",
        name="api_key",
    )
    print(f"  {auth_query}")

    # Build request to see how auth is applied
    print("\n→ Request Building Example:")
    builder = RequestBuilder(base_url="https://api.example.com")
    request = builder.build_request(endpoint=endpoint)

    # Apply auth to headers/params
    headers = {}
    params = {}
    auth_header.apply(headers, params)

    print(f"  Headers: {headers}")
    print(f"  Query Params: {params}")


def example4_parameter_locations():
    """
    Example 4: Handling different parameter locations.

    Demonstrates how parameters in different locations (path, query, header, body)
    are handled during request building.
    """
    print("\n" + "=" * 70)
    print("Example 4: Different Parameter Locations")
    print("=" * 70)

    from adapter.parsing.canonical_models import (
        CanonicalEndpoint,
        CanonicalParameter,
        DataType,
        ParameterLocation,
    )

    # Define endpoint with parameters in all locations
    endpoint = CanonicalEndpoint(
        name="update_user",
        path="/users/{user_id}",
        method="PATCH",
        description="Update user information",
        parameters=[
            CanonicalParameter(
                name="user_id",
                location=ParameterLocation.PATH,
                type=DataType.STRING,
                required=True,
                description="User ID in path",
            ),
            CanonicalParameter(
                name="include",
                location=ParameterLocation.QUERY,
                type=DataType.STRING,
                required=False,
                description="Include related data",
            ),
            CanonicalParameter(
                name="x_request_id",
                location=ParameterLocation.HEADER,
                type=DataType.STRING,
                required=False,
                description="Request tracking ID",
            ),
            CanonicalParameter(
                name="name",
                location=ParameterLocation.BODY,
                type=DataType.STRING,
                required=False,
                description="User's new name",
            ),
            CanonicalParameter(
                name="email",
                location=ParameterLocation.BODY,
                type=DataType.STRING,
                required=False,
                description="User's new email",
            ),
        ],
    )

    # Build request with all parameter types
    builder = RequestBuilder(base_url="https://api.example.com")

    parameters = {
        "user_id": "123",
        "include": "profile",
        "x_request_id": "req-abc-123",
        "name": "John Doe",
        "email": "john@example.com",
    }

    request = builder.build_request(endpoint=endpoint, parameters=parameters)

    print(f"\n✓ Endpoint: {endpoint.method} {endpoint.path}")
    print(f"\n✓ Built Request:")
    print(f"  URL: {request['url']}")
    print(f"  Method: {request['method']}")
    print(f"  Headers: {request['headers']}")
    print(f"  Query Params: {request['query_params']}")
    print(f"  Body: {request['body']}")


def example5_error_handling():
    """
    Example 5: Error handling and retries.

    Demonstrates how the executor handles errors and retries.
    """
    print("\n" + "=" * 70)
    print("Example 5: Error Handling and Retries")
    print("=" * 70)

    from adapter.parsing.canonical_models import (
        CanonicalEndpoint,
        DataType,
        ParameterLocation,
    )

    endpoint = CanonicalEndpoint(
        name="test_endpoint",
        path="/test",
        method="GET",
        description="Test endpoint",
        parameters=[],
    )

    # Configure executor with retry settings
    executor = APIExecutor(
        base_url="https://httpbin.org",
        max_retries=3,
        retry_backoff=0.5,
        retry_on_status_codes=[429, 500, 502, 503, 504],
        timeout=10,
    )

    print(f"\n✓ Executor Configuration:")
    print(f"  Max Retries: {executor.max_retries}")
    print(f"  Retry Backoff: {executor.retry_backoff}s (exponential)")
    print(f"  Retry on Status Codes: {executor.retry_on_status_codes}")
    print(f"  Timeout: {executor.timeout}s")

    # Try a non-existent endpoint to trigger an error
    endpoint_404 = CanonicalEndpoint(
        name="nonexistent",
        path="/status/404",
        method="GET",
        description="Non-existent endpoint",
        parameters=[],
    )

    print(f"\n→ Testing 404 Error (no retry):")
    result = executor.execute(endpoint=endpoint_404)
    print(f"  Success: {result.success}")
    print(f"  Status Code: {result.response.status_code}")
    print(f"  Attempts: {result.attempts} (404 not retried)")

    # Try an endpoint that returns 500 (will retry)
    endpoint_500 = CanonicalEndpoint(
        name="server_error",
        path="/status/500",
        method="GET",
        description="Server error endpoint",
        parameters=[],
    )

    print(f"\n→ Testing 500 Error (will retry):")
    result = executor.execute(endpoint=endpoint_500)
    print(f"  Success: {result.success}")
    print(f"  Status Code: {result.response.status_code}")
    print(f"  Attempts: {result.attempts} (500 triggers retries)")
    print(f"  Error: {result.response.error}")


def example6_complete_workflow():
    """
    Example 6: Complete workflow - Load, Normalize, Generate, Execute.

    Demonstrates the end-to-end workflow from OpenAPI spec to API execution.
    """
    print("\n" + "=" * 70)
    print("Example 6: Complete Workflow (OpenAPI → Execution)")
    print("=" * 70)

    # Step 1: Load OpenAPI spec
    print("\n→ Step 1: Load OpenAPI Specification")
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    print(f"  ✓ Loaded OpenAPI spec")

    # Step 2: Normalize to canonical format
    print("\n→ Step 2: Normalize to Canonical Format")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    print(f"  ✓ Normalized {len(endpoints)} endpoints")

    # Step 3: Generate MCP tools (optional, for completeness)
    print("\n→ Step 3: Generate MCP Tools")
    generator = ToolGenerator(api_name="petstore")
    tools = generator.generate_tools(endpoints)
    registry = ToolRegistry(name="Petstore API")
    registry.add_tools(tools)
    print(f"  ✓ Generated {len(tools)} MCP tools")

    # Step 4: Execute an API call
    print("\n→ Step 4: Execute API Call")

    # Find the GET /pet/{petId} endpoint
    get_pet_endpoint = None
    for endpoint in endpoints:
        if "get_pet" in endpoint.name and "{pet_id}" in endpoint.path.lower():
            get_pet_endpoint = endpoint
            break

    if get_pet_endpoint:
        print(f"  ✓ Found endpoint: {get_pet_endpoint.name}")
        print(f"    Path: {get_pet_endpoint.method} {get_pet_endpoint.path}")

        # Create executor
        executor = APIExecutor(
            base_url="https://petstore3.swagger.io/api/v3",
            auth=NoAuth(),
        )

        # Execute with a known pet ID
        result = executor.execute(
            endpoint=get_pet_endpoint,
            parameters={"pet_id": "1"},
        )

        print(f"\n  ✓ Execution Result:")
        print(f"    Success: {result.success}")
        print(f"    Status: {result.response.status_code}")
        print(f"    Time: {result.execution_time_ms:.2f}ms")

        if result.success and result.response.data:
            print(f"    Data: {result.response.data}")
        else:
            print(f"    Note: Pet ID 1 may not exist (expected)")
    else:
        print("  ✗ Could not find get_pet endpoint")


def main():
    """Run all Phase 3 examples."""
    print("\n" + "=" * 70)
    print("Phase 3: Runtime Execution Engine Examples")
    print("=" * 70)
    print(
        "\nThese examples demonstrate the runtime execution capabilities:\n"
        "- Building HTTP requests from canonical endpoints\n"
        "- Various authentication methods\n"
        "- Parameter handling (path, query, header, body)\n"
        "- Error handling and automatic retries\n"
        "- Complete OpenAPI → Execution workflow"
    )

    try:
        example1_basic_execution()
        example2_bearer_auth()
        example3_api_key_auth()
        example4_parameter_locations()
        example5_error_handling()
        example6_complete_workflow()

        print("\n" + "=" * 70)
        print("✓ All examples completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
