"""
Custom execution handler for ODS MCP server with conditional authentication.
"""

import logging
from typing import Any, Dict

from adapter.server.execution_handler import ExecutionHandler
from ods_auth_resolver import ODSAuthResolver

logger = logging.getLogger(__name__)


class ODSExecutionHandler(ExecutionHandler):
    """
    Extended ExecutionHandler with conditional authentication for ODS API.

    This handler determines the appropriate authentication method based on
    the tool being called and its arguments, then temporarily swaps the
    executor's auth handler before execution.
    """

    def __init__(
        self,
        tool_provider,
        executor,
        endpoints,
        auth_resolver: ODSAuthResolver,
    ):
        """
        Initialize the ODS execution handler.

        Args:
            tool_provider: ToolProvider for tool lookup
            executor: APIExecutor for making API calls
            endpoints: List of CanonicalEndpoint objects
            auth_resolver: ODSAuthResolver for determining auth requirements
        """
        super().__init__(tool_provider, executor, endpoints)
        self.auth_resolver = auth_resolver
        logger.info("ODSExecutionHandler initialized with conditional auth")

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool with conditional authentication.

        This method:
        1. Determines the required auth handler based on tool and arguments
        2. Temporarily swaps the executor's auth handler
        3. Calls the parent execute_tool method
        4. Restores the original auth handler

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments (parameter values)

        Returns:
            Execution result in MCP format
        """
        # Resolve authentication requirement
        required_auth = self.auth_resolver.resolve_auth(tool_name, arguments)

        # Save original auth handler
        original_auth = self.executor.auth

        try:
            # Swap to required auth handler
            self.executor.auth = required_auth
            logger.debug(
                f"Using auth handler: {required_auth.__class__.__name__} "
                f"for tool: {tool_name}"
            )

            # Execute with parent method
            result = super().execute_tool(tool_name, arguments)

            return result

        finally:
            # Always restore original auth handler
            self.executor.auth = original_auth
