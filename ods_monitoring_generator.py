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

        for endpoint in catalog_endpoints:
            # Only clone dataset-specific operations (skip catalog-level operations)
            if not self._is_dataset_operation(endpoint):
                continue

            # Clone and modify the endpoint
            monitoring_endpoint = self._clone_to_monitoring(endpoint)
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

        # Update description
        if monitoring.description:
            monitoring.description = (
                f"[MONITORING API] {monitoring.description}"
            )
        else:
            monitoring.description = (
                f"[MONITORING API] {endpoint.summary or 'Monitoring endpoint'}"
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
