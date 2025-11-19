"""
Response processing for HTTP API responses.

Handles response parsing, error detection, and data extraction.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ProcessedResponse:
    """
    Processed HTTP response.

    Attributes:
        status_code: HTTP status code
        success: Whether the request was successful
        data: Parsed response data (usually dict or list)
        raw_text: Raw response text
        headers: Response headers
        error: Error message if the request failed
    """

    status_code: int
    success: bool
    data: Optional[Any] = None
    raw_text: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "status_code": self.status_code,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "headers": self.headers,
        }


class ResponseProcessor:
    """
    Processes HTTP responses from API calls.

    Handles:
    - JSON parsing
    - Status code validation
    - Error detection and extraction
    - Data normalization

    Examples:
        >>> processor = ResponseProcessor()
        >>> response = requests.get("https://api.example.com/users")
        >>> result = processor.process(response)
        >>> if result.success:
        ...     print(result.data)
    """

    def __init__(
        self,
        success_codes: Optional[list] = None,
        auto_parse_json: bool = True,
    ):
        """
        Initialize the response processor.

        Args:
            success_codes: List of HTTP status codes considered successful
                          (default: 200-299)
            auto_parse_json: Automatically parse JSON responses
        """
        self.success_codes = success_codes or list(range(200, 300))
        self.auto_parse_json = auto_parse_json

    def process(self, response: Any) -> ProcessedResponse:
        """
        Process an HTTP response.

        Args:
            response: Response object (requests.Response or similar)

        Returns:
            Processed response with parsed data
        """
        status_code = response.status_code
        success = status_code in self.success_codes

        # Get headers
        headers = dict(response.headers) if hasattr(response, "headers") else {}

        # Get raw text
        raw_text = response.text if hasattr(response, "text") else str(response)

        # Parse response data
        data = None
        error = None

        if success:
            # Try to parse successful response
            data = self._parse_data(response, headers)
        else:
            # Extract error information
            error = self._extract_error(response, status_code, raw_text)
            # Some APIs return error details in response body
            data = self._parse_data(response, headers)

        return ProcessedResponse(
            status_code=status_code,
            success=success,
            data=data,
            raw_text=raw_text,
            headers=headers,
            error=error,
        )

    def _parse_data(self, response: Any, headers: Dict[str, str]) -> Optional[Any]:
        """
        Parse response data based on content type.

        Args:
            response: Response object
            headers: Response headers

        Returns:
            Parsed data (dict, list, or string)
        """
        if not self.auto_parse_json:
            return response.text if hasattr(response, "text") else str(response)

        # Check content type
        content_type = headers.get("Content-Type", "").lower()

        # Try JSON parsing
        if "application/json" in content_type or self._looks_like_json(response):
            try:
                return response.json() if hasattr(response, "json") else json.loads(response.text)
            except (json.JSONDecodeError, ValueError, AttributeError):
                # Fall back to text
                return response.text if hasattr(response, "text") else str(response)

        # Return raw text for other content types
        return response.text if hasattr(response, "text") else str(response)

    def _looks_like_json(self, response: Any) -> bool:
        """
        Heuristic to detect if response might be JSON.

        Args:
            response: Response object

        Returns:
            True if response looks like JSON
        """
        if not hasattr(response, "text"):
            return False

        text = response.text.strip()
        return text.startswith(("{", "["))

    def _extract_error(
        self, response: Any, status_code: int, raw_text: str
    ) -> str:
        """
        Extract error message from failed response.

        Args:
            response: Response object
            status_code: HTTP status code
            raw_text: Raw response text

        Returns:
            Error message string
        """
        # Try to parse error from JSON response
        try:
            if hasattr(response, "json"):
                error_data = response.json()
            else:
                error_data = json.loads(raw_text)

            # Common error message fields
            for field in ["error", "message", "error_description", "detail", "title"]:
                if field in error_data:
                    error_value = error_data[field]
                    if isinstance(error_value, str):
                        return error_value
                    elif isinstance(error_value, dict) and "message" in error_value:
                        return error_value["message"]

            # If no standard field found, return the whole error object
            return json.dumps(error_data)

        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

        # Fall back to status code and raw text
        if raw_text and len(raw_text) < 500:
            return f"HTTP {status_code}: {raw_text}"

        return f"HTTP {status_code}: Request failed"

    def is_success(self, response: Any) -> bool:
        """
        Check if a response is successful.

        Args:
            response: Response object

        Returns:
            True if successful
        """
        return response.status_code in self.success_codes
