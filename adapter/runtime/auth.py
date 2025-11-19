"""
Authentication handlers for REST API calls.

Supports various authentication methods including API keys, Bearer tokens,
Basic auth, and OAuth2.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from enum import Enum


class AuthType(Enum):
    """Supported authentication types."""

    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class AuthHandler(ABC):
    """
    Base class for authentication handlers.

    All authentication handlers must implement the apply() method to add
    authentication credentials to the request.
    """

    @abstractmethod
    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """
        Apply authentication to the request.

        Args:
            headers: Request headers (modified in-place)
            params: Request parameters (modified in-place)
        """
        pass

    @abstractmethod
    def get_type(self) -> AuthType:
        """Return the authentication type."""
        pass


class NoAuth(AuthHandler):
    """No authentication required."""

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """No-op - no authentication to apply."""
        pass

    def get_type(self) -> AuthType:
        return AuthType.NONE

    def __repr__(self) -> str:
        return "NoAuth()"


class APIKeyAuth(AuthHandler):
    """
    API Key authentication.

    Supports API keys in headers, query parameters, or cookies.

    Examples:
        >>> # Header-based API key
        >>> auth = APIKeyAuth(key="my-api-key", location="header", name="X-API-Key")
        >>>
        >>> # Query parameter API key
        >>> auth = APIKeyAuth(key="my-api-key", location="query", name="api_key")
    """

    def __init__(
        self,
        key: str,
        location: str = "header",
        name: str = "X-API-Key",
    ):
        """
        Initialize API key authentication.

        Args:
            key: The API key value
            location: Where to send the key ("header", "query", or "cookie")
            name: The parameter/header name for the API key
        """
        self.key = key
        self.location = location.lower()
        self.name = name

        if self.location not in ("header", "query", "cookie"):
            raise ValueError(f"Invalid location '{location}'. Must be 'header', 'query', or 'cookie'")

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """Apply API key to the request."""
        if self.location == "header":
            headers[self.name] = self.key
        elif self.location == "query":
            params[self.name] = self.key
        elif self.location == "cookie":
            # Add to Cookie header
            cookie_value = f"{self.name}={self.key}"
            if "Cookie" in headers:
                headers["Cookie"] += f"; {cookie_value}"
            else:
                headers["Cookie"] = cookie_value

    def get_type(self) -> AuthType:
        return AuthType.API_KEY

    def __repr__(self) -> str:
        return f"APIKeyAuth(location='{self.location}', name='{self.name}')"


class BearerAuth(AuthHandler):
    """
    Bearer token authentication.

    Adds an Authorization header with a Bearer token.

    Examples:
        >>> auth = BearerAuth(token="eyJhbGciOiJIUzI1NiIs...")
    """

    def __init__(self, token: str):
        """
        Initialize Bearer token authentication.

        Args:
            token: The bearer token
        """
        self.token = token

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """Apply Bearer token to the Authorization header."""
        headers["Authorization"] = f"Bearer {self.token}"

    def get_type(self) -> AuthType:
        return AuthType.BEARER

    def __repr__(self) -> str:
        return "BearerAuth(token='***')"


class BasicAuth(AuthHandler):
    """
    HTTP Basic authentication.

    Adds an Authorization header with Base64-encoded credentials.

    Examples:
        >>> auth = BasicAuth(username="user", password="pass")
    """

    def __init__(self, username: str, password: str):
        """
        Initialize Basic authentication.

        Args:
            username: The username
            password: The password
        """
        self.username = username
        self.password = password

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """Apply Basic auth to the Authorization header."""
        import base64

        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"

    def get_type(self) -> AuthType:
        return AuthType.BASIC

    def __repr__(self) -> str:
        return f"BasicAuth(username='{self.username}')"


class OAuth2Auth(AuthHandler):
    """
    OAuth2 authentication.

    Adds an Authorization header with an OAuth2 access token.

    Note: This handler assumes you already have a valid access token.
    Token acquisition/refresh is outside the scope of this handler.

    Examples:
        >>> auth = OAuth2Auth(access_token="ya29.a0AfH6SMB...")
    """

    def __init__(
        self,
        access_token: str,
        token_type: str = "Bearer",
    ):
        """
        Initialize OAuth2 authentication.

        Args:
            access_token: The OAuth2 access token
            token_type: The token type (usually "Bearer")
        """
        self.access_token = access_token
        self.token_type = token_type

    def apply(self, headers: Dict[str, str], params: Dict[str, str]) -> None:
        """Apply OAuth2 token to the Authorization header."""
        headers["Authorization"] = f"{self.token_type} {self.access_token}"

    def get_type(self) -> AuthType:
        return AuthType.OAUTH2

    def __repr__(self) -> str:
        return f"OAuth2Auth(token_type='{self.token_type}')"
