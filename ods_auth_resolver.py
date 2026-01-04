"""
Authentication resolver for ODS MCP server.

Determines which authentication handler to use based on the tool being called
and its arguments.
"""

import os
import logging
from typing import Optional, Dict, Any

from adapter.runtime.auth import AuthHandler, NoAuth, APIKeyAuth

logger = logging.getLogger(__name__)


class ODSAuthResolver:
    """
    Resolves authentication requirements for ODS API calls.

    Determines when to use API key authentication vs no auth based on:
    1. Dataset ID in arguments (monitoring datasets require auth)
    2. Tool name patterns (monitoring/analytics tools require auth)
    """

    # Dataset IDs that require authentication
    AUTH_REQUIRED_DATASETS = {
        'ods-api-monitoring',
        'ods-datasets-monitoring',
    }

    # Tool name patterns that suggest authentication needed
    AUTH_REQUIRED_KEYWORDS = {
        'monitoring',
        'analytics',
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the auth resolver.

        Args:
            api_key: API key for authenticated requests.
                    If None, will try to load from ODS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('ODS_API_KEY')

        if not self.api_key:
            logger.warning(
                "No API key provided. Authenticated endpoints will fail. "
                "Set ODS_API_KEY environment variable or pass api_key parameter."
            )

        # Pre-create auth handlers
        self.no_auth = NoAuth()
        self.api_key_auth = APIKeyAuth(
            key=self.api_key or "",
            location="query",
            name="apikey"
        ) if self.api_key else None

        logger.info(
            f"ODSAuthResolver initialized (API key: {'present' if self.api_key else 'missing'})"
        )

    def resolve_auth(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> AuthHandler:
        """
        Determine which auth handler to use for a given tool call.

        Args:
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool

        Returns:
            Appropriate AuthHandler (APIKeyAuth or NoAuth)
        """
        # Check if dataset_id in arguments requires auth
        dataset_id = arguments.get('dataset_id')
        if dataset_id and dataset_id in self.AUTH_REQUIRED_DATASETS:
            logger.info(
                f"Auth required for dataset '{dataset_id}' "
                f"(tool: {tool_name})"
            )
            if self.api_key_auth:
                return self.api_key_auth
            else:
                logger.warning(
                    f"Dataset '{dataset_id}' requires auth but no API key available"
                )
                return self.no_auth

        # Check if tool name suggests authentication needed
        tool_name_lower = tool_name.lower()
        for keyword in self.AUTH_REQUIRED_KEYWORDS:
            if keyword in tool_name_lower:
                logger.info(
                    f"Auth required based on tool name pattern '{keyword}' "
                    f"(tool: {tool_name})"
                )
                if self.api_key_auth:
                    return self.api_key_auth
                else:
                    logger.warning(
                        f"Tool '{tool_name}' suggests auth needed but no API key available"
                    )
                    return self.no_auth

        # Default: no authentication required
        logger.debug(f"No auth required for tool '{tool_name}'")
        return self.no_auth

    def has_api_key(self) -> bool:
        """Check if API key is available."""
        return self.api_key is not None and len(self.api_key) > 0
