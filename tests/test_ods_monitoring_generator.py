"""
Tests for ODS monitoring endpoint generator.

Verifies that catalog endpoints are correctly cloned to monitoring endpoints
with appropriate path, security, and naming modifications.
"""

import pytest
from adapter.parsing.canonical_models import (
    CanonicalEndpoint,
    CanonicalParameter,
    ParameterLocation,
    DataType,
)
from ods_monitoring_generator import ODSMonitoringGenerator


@pytest.fixture
def monitoring_generator():
    """Create a monitoring generator instance."""
    return ODSMonitoringGenerator()


@pytest.fixture
def sample_catalog_endpoints():
    """Create sample catalog endpoints for testing."""
    return [
        # Dataset-specific endpoint (should be cloned)
        CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            description="Perform a query on dataset records.",
            parameters=[
                CanonicalParameter(
                    name="dataset_id",
                    location=ParameterLocation.PATH,
                    type=DataType.STRING,
                    required=True,
                    description="Dataset identifier",
                ),
                CanonicalParameter(
                    name="limit",
                    location=ParameterLocation.QUERY,
                    type=DataType.NUMBER,
                    required=False,
                    description="Number of items to return",
                    default=10,
                ),
            ],
            tags=["catalog", "records"],
            security=[],  # Public endpoint
        ),
        # Export endpoint (should be cloned)
        CanonicalEndpoint(
            name="export_records_parquet",
            method="GET",
            path="/catalog/datasets/{dataset_id}/exports/parquet",
            description="Export a dataset in Parquet.",
            summary="Export dataset as Parquet",
            parameters=[
                CanonicalParameter(
                    name="dataset_id",
                    location=ParameterLocation.PATH,
                    type=DataType.STRING,
                    required=True,
                ),
            ],
            tags=["catalog", "export"],
            security=[],
        ),
        # Catalog-level endpoint (should NOT be cloned)
        CanonicalEndpoint(
            name="get_datasets",
            method="GET",
            path="/catalog/datasets",
            description="Retrieve available datasets.",
            parameters=[
                CanonicalParameter(
                    name="limit",
                    location=ParameterLocation.QUERY,
                    type=DataType.NUMBER,
                    required=False,
                ),
            ],
            tags=["catalog"],
            security=[],
        ),
    ]


class TestODSMonitoringGenerator:
    """Test suite for monitoring endpoint generator."""

    def test_is_dataset_operation_with_path_param(self, monitoring_generator):
        """Test identification of dataset operations via path parameter."""
        endpoint = CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            parameters=[],
        )

        assert monitoring_generator._is_dataset_operation(endpoint) is True

    def test_is_dataset_operation_with_parameter(self, monitoring_generator):
        """Test identification of dataset operations via parameter list."""
        endpoint = CanonicalEndpoint(
            name="get_dataset",
            method="GET",
            path="/catalog/datasets/{id}",
            parameters=[
                CanonicalParameter(
                    name="dataset_id",
                    location=ParameterLocation.PATH,
                    type=DataType.STRING,
                    required=True,
                )
            ],
        )

        assert monitoring_generator._is_dataset_operation(endpoint) is True

    def test_is_dataset_operation_catalog_level(self, monitoring_generator):
        """Test that catalog-level operations are not identified as dataset ops."""
        endpoint = CanonicalEndpoint(
            name="get_datasets",
            method="GET",
            path="/catalog/datasets",
            parameters=[],
        )

        assert monitoring_generator._is_dataset_operation(endpoint) is False

    def test_clone_to_monitoring_path_modification(self, monitoring_generator):
        """Test that path is correctly modified from /catalog/ to /monitoring/."""
        catalog_endpoint = CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            parameters=[],
        )

        monitoring = monitoring_generator._clone_to_monitoring(catalog_endpoint)

        assert monitoring.path == "/monitoring/datasets/{dataset_id}/records"

    def test_clone_to_monitoring_name_modification(self, monitoring_generator):
        """Test that name is prefixed with 'monitoring_'."""
        catalog_endpoint = CanonicalEndpoint(
            name="export_records_parquet",
            method="GET",
            path="/catalog/datasets/{dataset_id}/exports/parquet",
            parameters=[],
        )

        monitoring = monitoring_generator._clone_to_monitoring(catalog_endpoint)

        assert monitoring.name == "monitoring_export_records_parquet"

    def test_clone_to_monitoring_security_added(self, monitoring_generator):
        """Test that API key security is added to monitoring endpoints."""
        catalog_endpoint = CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            parameters=[],
            security=[],  # Public endpoint
        )

        monitoring = monitoring_generator._clone_to_monitoring(catalog_endpoint)

        assert monitoring.security == [{"apikey": []}]

    def test_clone_to_monitoring_description_updated(self, monitoring_generator):
        """Test that description is updated to mention monitoring."""
        catalog_endpoint = CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            description="Perform a query on dataset records.",
            parameters=[],
        )

        monitoring = monitoring_generator._clone_to_monitoring(catalog_endpoint)

        assert "[MONITORING API]" in monitoring.description
        assert "Perform a query on dataset records." in monitoring.description

    def test_clone_to_monitoring_tags_updated(self, monitoring_generator):
        """Test that tags are updated with monitoring."""
        catalog_endpoint = CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            parameters=[],
            tags=["catalog", "records"],
        )

        monitoring = monitoring_generator._clone_to_monitoring(catalog_endpoint)

        assert "monitoring" in monitoring.tags
        assert "records" in monitoring.tags
        # 'catalog' should be replaced with 'monitoring'
        assert monitoring.tags.count("monitoring") >= 1

    def test_clone_to_monitoring_parameters_preserved(self, monitoring_generator):
        """Test that parameters are preserved in cloning."""
        catalog_endpoint = CanonicalEndpoint(
            name="get_records",
            method="GET",
            path="/catalog/datasets/{dataset_id}/records",
            parameters=[
                CanonicalParameter(
                    name="dataset_id",
                    location=ParameterLocation.PATH,
                    type=DataType.STRING,
                    required=True,
                ),
                CanonicalParameter(
                    name="limit",
                    location=ParameterLocation.QUERY,
                    type=DataType.NUMBER,
                    required=False,
                    default=10,
                ),
            ],
        )

        monitoring = monitoring_generator._clone_to_monitoring(catalog_endpoint)

        assert len(monitoring.parameters) == 2
        assert monitoring.parameters[0].name == "dataset_id"
        assert monitoring.parameters[1].name == "limit"
        assert monitoring.parameters[1].default == 10

    def test_clone_to_monitoring_original_unchanged(self, monitoring_generator):
        """Test that original endpoint is not modified during cloning."""
        original_path = "/catalog/datasets/{dataset_id}/records"
        original_name = "get_records"
        catalog_endpoint = CanonicalEndpoint(
            name=original_name,
            method="GET",
            path=original_path,
            parameters=[],
            security=[],
        )

        monitoring_generator._clone_to_monitoring(catalog_endpoint)

        # Original should be unchanged
        assert catalog_endpoint.path == original_path
        assert catalog_endpoint.name == original_name
        assert catalog_endpoint.security == []

    def test_generate_monitoring_endpoints_filtering(
        self, monitoring_generator, sample_catalog_endpoints
    ):
        """Test that only dataset operations are cloned."""
        monitoring_endpoints = monitoring_generator.generate_monitoring_endpoints(
            sample_catalog_endpoints
        )

        # Should clone 2 dataset endpoints, skip 1 catalog-level endpoint
        assert len(monitoring_endpoints) == 2

        # Check that the right endpoints were cloned
        names = {ep.name for ep in monitoring_endpoints}
        assert "monitoring_get_records" in names
        assert "monitoring_export_records_parquet" in names

    def test_generate_monitoring_endpoints_all_modified(
        self, monitoring_generator, sample_catalog_endpoints
    ):
        """Test that all generated endpoints have monitoring modifications."""
        monitoring_endpoints = monitoring_generator.generate_monitoring_endpoints(
            sample_catalog_endpoints
        )

        for endpoint in monitoring_endpoints:
            # All should have /monitoring/ in path
            assert "/monitoring/" in endpoint.path
            # All should start with monitoring_
            assert endpoint.name.startswith("monitoring_")
            # All should have security
            assert endpoint.security == [{"apikey": []}]
            # All should have monitoring tag
            assert "monitoring" in endpoint.tags

    def test_generate_monitoring_endpoints_empty_input(self, monitoring_generator):
        """Test handling of empty endpoint list."""
        monitoring_endpoints = monitoring_generator.generate_monitoring_endpoints([])

        assert monitoring_endpoints == []

    def test_generate_monitoring_endpoints_no_dataset_ops(self, monitoring_generator):
        """Test handling when no dataset operations are present."""
        catalog_only = [
            CanonicalEndpoint(
                name="get_datasets",
                method="GET",
                path="/catalog/datasets",
                parameters=[],
            ),
            CanonicalEndpoint(
                name="get_facets",
                method="GET",
                path="/catalog/facets",
                parameters=[],
            ),
        ]

        monitoring_endpoints = monitoring_generator.generate_monitoring_endpoints(
            catalog_only
        )

        assert monitoring_endpoints == []
