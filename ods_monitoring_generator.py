"""
Monitoring endpoint generator for ODS MCP server.

Generates monitoring API endpoints by cloning catalog endpoints and modifying
them to use the /monitoring/ path prefix with API key authentication.
"""

import logging
from typing import List
from copy import deepcopy

from adapter.parsing.canonical_models import CanonicalEndpoint

logger = logging.getLogger(__name__)


class ODSMonitoringGenerator:
    """
    Generates monitoring endpoints by cloning catalog dataset endpoints.

    The ODS monitoring API mirrors the catalog dataset API structure but:
    1. Uses /monitoring/ instead of /catalog/ path prefix
    2. Requires API key authentication
    3. Only exposes specific datasets (ods-api-monitoring, ods-datasets-monitoring)

    Since the OpenAPI spec doesn't include monitoring endpoints, we generate
    them by cloning the catalog dataset endpoints and applying these modifications.
    """

    # Operations to clone from catalog to monitoring
    # These are the operation IDs from the OpenAPI spec
    MONITORING_OPERATIONS = {
        'get_records',
        'list_dataset_export_formats',
        'export_records',
        'export_records_csv',
        'export_records_parquet',
        'export_records_gpx',
        'get_dataset',
        'get_records_facets',
        'get_dataset_attachments',
        'get_record',
    }

    def __init__(self):
        """Initialize the monitoring generator."""
        logger.info("ODSMonitoringGenerator initialized")

    def generate_monitoring_endpoints(
        self,
        catalog_endpoints: List[CanonicalEndpoint]
    ) -> List[CanonicalEndpoint]:
        """
        Generate monitoring endpoints from catalog endpoints.

        Args:
            catalog_endpoints: List of catalog endpoints to clone

        Returns:
            List of monitoring endpoints with modified paths and security
        """
        monitoring_endpoints = []

        # Find the generic export_records endpoint to extract common parameters
        export_records_endpoint = None
        for endpoint in catalog_endpoints:
            if endpoint.name == 'export_records':
                export_records_endpoint = endpoint
                break

        for endpoint in catalog_endpoints:
            # Only clone dataset-specific operations (skip catalog-level operations)
            if not self._is_dataset_operation(endpoint):
                continue

            # Clone and modify the endpoint
            monitoring_endpoint = self._clone_to_monitoring(endpoint)

            # Merge common export parameters for format-specific endpoints
            if export_records_endpoint and self._is_format_specific_export(endpoint):
                self._merge_common_export_params(
                    monitoring_endpoint,
                    export_records_endpoint
                )
                logger.debug(
                    f"Merged common export params into {monitoring_endpoint.name}"
                )

            monitoring_endpoints.append(monitoring_endpoint)
            logger.debug(
                f"Cloned {endpoint.name} -> {monitoring_endpoint.name}"
            )

        logger.info(
            f"Generated {len(monitoring_endpoints)} monitoring endpoints "
            f"from {len(catalog_endpoints)} catalog endpoints"
        )

        return monitoring_endpoints

    def _is_dataset_operation(self, endpoint: CanonicalEndpoint) -> bool:
        """
        Check if an endpoint is a dataset-specific operation.

        Dataset operations have paths like:
        - /catalog/datasets/{dataset_id}/...

        Catalog-level operations (which we skip) have paths like:
        - /catalog/datasets
        - /catalog/exports
        - /catalog/facets

        Args:
            endpoint: Endpoint to check

        Returns:
            True if endpoint is dataset-specific, False otherwise
        """
        # Check if path contains dataset_id parameter
        if '{dataset_id}' in endpoint.path:
            return True

        # Check if any parameter is named dataset_id
        for param in endpoint.parameters:
            if param.name == 'dataset_id':
                return True

        return False

    def _clone_to_monitoring(
        self,
        endpoint: CanonicalEndpoint
    ) -> CanonicalEndpoint:
        """
        Clone a catalog endpoint to a monitoring endpoint.

        Modifications:
        1. Path: /catalog/ -> /monitoring/
        2. Name: add monitoring_ prefix
        3. Security: add apikey requirement
        4. Description: update to mention monitoring
        5. Tags: replace 'catalog' with 'monitoring'

        Args:
            endpoint: Catalog endpoint to clone

        Returns:
            New monitoring endpoint
        """
        # Deep copy to avoid modifying original
        monitoring = deepcopy(endpoint)

        # Modify path
        monitoring.path = endpoint.path.replace('/catalog/', '/monitoring/')

        # Modify name
        monitoring.name = f"monitoring_{endpoint.name}"

        # Add API key security requirement
        # Format matches OpenAPI security schemes
        monitoring.security = [{"apikey": []}]

        # Update description with usage guidance
        base_desc = monitoring.description or endpoint.summary or 'Monitoring endpoint'
        monitoring.description = (
            f"[MONITORING API] {base_desc}\n\n"
            f"Use this tool for monitoring datasets (ods-api-monitoring, ods-datasets-monitoring). "
            f"For public datasets, use the corresponding catalog tool without 'monitoring' in the name. "
            f"This endpoint requires API key authentication."
        )

        # Update tags
        if monitoring.tags:
            monitoring.tags = [
                tag.replace('catalog', 'monitoring') if tag == 'catalog' else tag
                for tag in monitoring.tags
            ]
            if 'monitoring' not in monitoring.tags:
                monitoring.tags.append('monitoring')
        else:
            monitoring.tags = ['monitoring']

        return monitoring

    def _is_format_specific_export(self, endpoint: CanonicalEndpoint) -> bool:
        """
        Check if an endpoint is a format-specific export endpoint.

        Format-specific endpoints are like:
        - export_records_csv
        - export_records_parquet
        - export_records_gpx

        Args:
            endpoint: Endpoint to check

        Returns:
            True if endpoint is format-specific export, False otherwise
        """
        format_specific_exports = [
            'export_records_csv',
            'export_records_parquet',
            'export_records_gpx'
        ]
        return endpoint.name in format_specific_exports

    def _merge_common_export_params(
        self,
        target_endpoint: CanonicalEndpoint,
        source_endpoint: CanonicalEndpoint
    ) -> None:
        """
        Merge common export parameters from source into target endpoint.

        This adds parameters like limit, order_by, where, select, etc. from the
        generic export_records endpoint into format-specific endpoints that are
        missing them.

        Args:
            target_endpoint: Endpoint to add parameters to (modified in-place)
            source_endpoint: Endpoint to copy parameters from (generic export_records)
        """
        # Parameters to merge (common export parameters)
        common_export_params = {
            'limit', 'offset', 'order_by', 'where', 'select',
            'exclude', 'refine', 'group_by', 'lang', 'timezone'
        }

        # Get existing parameter names in target
        existing_param_names = {p.name for p in target_endpoint.parameters}

        # Copy missing common parameters from source
        for param in source_endpoint.parameters:
            if param.name in common_export_params and param.name not in existing_param_names:
                # Deep copy the parameter to avoid shared references
                target_endpoint.parameters.append(deepcopy(param))
