"""
Integration tests for ODS MCP server with conditional authentication.

Tests against the live ODS API to verify:
1. Public datasets work without API key
2. Monitoring datasets require API key
3. Conditional auth resolver works correctly
"""

import os
import pytest
from unittest.mock import Mock

from adapter import ToolRegistry, APIExecutor, NoAuth
from adapter.server.tool_provider import ToolProvider
from ods_auth_resolver import ODSAuthResolver
from ods_execution_handler import ODSExecutionHandler


class TestODSAuthResolver:
    """Test the ODSAuthResolver logic."""

    def test_resolver_initialization_with_key(self):
        """Test resolver initializes with API key."""
        resolver = ODSAuthResolver(api_key="test_key")
        assert resolver.has_api_key()
        assert resolver.api_key == "test_key"

    def test_resolver_initialization_from_env(self, monkeypatch):
        """Test resolver loads API key from environment."""
        monkeypatch.setenv('ODS_API_KEY', 'env_key')
        resolver = ODSAuthResolver()
        assert resolver.has_api_key()
        assert resolver.api_key == "env_key"

    def test_resolver_no_key(self):
        """Test resolver handles missing API key gracefully."""
        # Clear environment variable if it exists
        resolver = ODSAuthResolver(api_key=None)
        assert not resolver.has_api_key()

    def test_resolve_auth_monitoring_dataset(self):
        """Test auth required for ods-api-monitoring dataset."""
        resolver = ODSAuthResolver(api_key="test_key")

        auth = resolver.resolve_auth(
            tool_name="ods_get_records",
            arguments={"dataset_id": "ods-api-monitoring"}
        )

        assert auth.get_type().value == "api_key"

    def test_resolve_auth_datasets_monitoring_dataset(self):
        """Test auth required for ods-datasets-monitoring dataset."""
        resolver = ODSAuthResolver(api_key="test_key")

        auth = resolver.resolve_auth(
            tool_name="ods_get_records",
            arguments={"dataset_id": "ods-datasets-monitoring"}
        )

        assert auth.get_type().value == "api_key"

    def test_resolve_auth_public_dataset(self):
        """Test no auth for public dataset."""
        resolver = ODSAuthResolver(api_key="test_key")

        auth = resolver.resolve_auth(
            tool_name="ods_get_records",
            arguments={"dataset_id": "public-transport-data"}
        )

        assert auth.get_type().value == "none"

    def test_resolve_auth_monitoring_keyword(self):
        """Test auth required for tool with 'monitoring' in name."""
        resolver = ODSAuthResolver(api_key="test_key")

        auth = resolver.resolve_auth(
            tool_name="ods_get_monitoring_analytics",
            arguments={}
        )

        assert auth.get_type().value == "api_key"

    def test_resolve_auth_analytics_keyword(self):
        """Test auth required for tool with 'analytics' in name."""
        resolver = ODSAuthResolver(api_key="test_key")

        auth = resolver.resolve_auth(
            tool_name="ods_export_analytics",
            arguments={}
        )

        assert auth.get_type().value == "api_key"

    def test_resolve_auth_no_key_available(self):
        """Test resolver falls back to NoAuth when API key missing."""
        resolver = ODSAuthResolver(api_key=None)

        # Should return NoAuth even for monitoring dataset
        auth = resolver.resolve_auth(
            tool_name="ods_get_records",
            arguments={"dataset_id": "ods-api-monitoring"}
        )

        assert auth.get_type().value == "none"


@pytest.mark.integration
class TestODSConditionalAuthIntegration:
    """Integration tests against live ODS API."""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        key = os.getenv('ODS_API_KEY')
        if not key:
            pytest.skip("ODS_API_KEY not set")
        return key

    @pytest.fixture
    def registry(self):
        """Create tool registry from live ODS API."""
        registry = ToolRegistry.create_from_openapi(
            source="https://opendata.westofengland-ca.gov.uk/api/explore/v2.1/swagger.json",
            name="West of England OpenDataSoft",
            api_name="ods",
            auto_detect_auth=True,
            include_metadata=True,
        )
        return registry

    @pytest.fixture
    def executor(self):
        """Create API executor."""
        return APIExecutor(
            base_url="https://opendata.westofengland-ca.gov.uk/api/explore/v2.1",
            auth=NoAuth(),
            timeout=30,
            max_retries=3,
        )

    @pytest.fixture
    def execution_handler(self, registry, executor, api_key):
        """Create custom execution handler with API key."""
        tool_provider = ToolProvider(registry)
        endpoints = registry.get_all_endpoints()
        auth_resolver = ODSAuthResolver(api_key=api_key)

        return ODSExecutionHandler(
            tool_provider=tool_provider,
            executor=executor,
            endpoints=endpoints,
            auth_resolver=auth_resolver,
        )

    @pytest.fixture
    def execution_handler_no_auth(self, registry, executor):
        """Create execution handler without API key."""
        tool_provider = ToolProvider(registry)
        endpoints = registry.get_all_endpoints()
        auth_resolver = ODSAuthResolver(api_key=None)

        return ODSExecutionHandler(
            tool_provider=tool_provider,
            executor=executor,
            endpoints=endpoints,
            auth_resolver=auth_resolver,
        )

    def test_public_dataset_no_auth_required(self, execution_handler):
        """Test that public datasets work without authentication."""
        # Call a public dataset endpoint (catalog query)
        result = execution_handler.execute_tool(
            tool_name="ods_get_datasets",
            arguments={"limit": 1}
        )

        # Should succeed
        assert not result.get("isError", True), f"Request failed: {result}"
        assert "content" in result
        assert len(result["content"]) > 0

    def test_monitoring_dataset_with_auth(self, execution_handler):
        """Test that monitoring dataset works with API key."""
        # Call monitoring dataset endpoint
        result = execution_handler.execute_tool(
            tool_name="ods_get_records",
            arguments={
                "dataset_id": "ods-api-monitoring",
                "limit": 1
            }
        )

        # Should succeed with auth
        assert not result.get("isError", True), f"Request failed: {result}"
        assert "content" in result

    def test_datasets_monitoring_with_auth(self, execution_handler):
        """Test that ods-datasets-monitoring dataset works with API key."""
        # Call monitoring dataset endpoint
        result = execution_handler.execute_tool(
            tool_name="ods_get_records",
            arguments={
                "dataset_id": "ods-datasets-monitoring",
                "limit": 1
            }
        )

        # Should succeed with auth
        assert not result.get("isError", True), f"Request failed: {result}"
        assert "content" in result

    def test_monitoring_dataset_without_auth_fails(self, execution_handler_no_auth):
        """Test that monitoring dataset fails without API key."""
        # Call monitoring dataset without auth
        result = execution_handler_no_auth.execute_tool(
            tool_name="ods_get_records",
            arguments={
                "dataset_id": "ods-api-monitoring",
                "limit": 1
            }
        )

        # Should fail (the API will likely return an error or empty result)
        # Note: The exact error format depends on the API's response to unauthorized requests
        # We check that either it's an error or the content indicates failure
        is_error = result.get("isError", False)
        has_error_content = any(
            "error" in str(content).lower() or
            "unauthorized" in str(content).lower() or
            "401" in str(content)
            for content in result.get("content", [])
        )

        # Either it should be marked as error, or contain error-related content
        assert is_error or has_error_content, (
            "Expected monitoring dataset to fail without auth, "
            f"but got: {result}"
        )
