"""MCP API client wrapper for calling REST endpoints.

Provides HTTP client for MCP tools to invoke REST API endpoints.
Handles authentication, error handling, and response parsing.
"""

import logging
from typing import Any

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class MCPAPIClient:
    """HTTP client for MCP tools to call REST API endpoints."""

    def __init__(self, api_url: str = "http://localhost:8000", token: str | None = None):
        """Initialize MCP API client.

        Args:
            api_url: Base URL for API server (default: http://localhost:8000)
            token: JWT token for authentication (optional, can be set later)
        """
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        if token:
            self._set_auth_header(token)

    def set_token(self, token: str) -> None:
        """Set JWT token for authentication.

        Args:
            token: JWT token string
        """
        self.token = token
        self._set_auth_header(token)

    def _set_auth_header(self, token: str) -> None:
        """Set Authorization header with Bearer token.

        Args:
            token: JWT token string
        """
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _handle_error(self, response: requests.Response, endpoint: str) -> dict[str, Any]:
        """Handle API error responses.

        Args:
            response: Response object
            endpoint: API endpoint called

        Returns:
            Error details dictionary

        Raises:
            ValueError: For error responses
        """
        try:
            error_data = response.json()
            detail = error_data.get("detail", "Unknown error")
        except Exception:
            detail = response.text or "Unknown error"

        error_msg = f"API error ({response.status_code}): {detail} [{endpoint}]"
        logger.error(error_msg)

        raise ValueError(error_msg) from None

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make GET request to API.

        Args:
            endpoint: API endpoint (e.g., /backends)
            params: Query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            ValueError: If request fails
        """
        url = f"{self.api_url}/api/v1{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return self._handle_error(response, endpoint)
        except RequestException as e:
            error_msg = f"Request failed: {str(e)} [{endpoint}]"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make POST request to API.

        Args:
            endpoint: API endpoint
            data: Request body as dictionary (or form data if files provided)
            files: Files to upload (multipart/form-data)

        Returns:
            Response JSON as dictionary

        Raises:
            ValueError: If request fails
        """
        url = f"{self.api_url}/api/v1{endpoint}"
        try:
            if files:
                # Use multipart form data with files
                response = self.session.post(url, data=data, files=files, timeout=10)
            else:
                # Use JSON body
                response = self.session.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return self._handle_error(response, endpoint)
        except RequestException as e:
            error_msg = f"Request failed: {str(e)} [{endpoint}]"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make PUT request to API.

        Args:
            endpoint: API endpoint
            data: Request body as dictionary

        Returns:
            Response JSON as dictionary

        Raises:
            ValueError: If request fails
        """
        url = f"{self.api_url}/api/v1{endpoint}"
        try:
            response = self.session.put(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return self._handle_error(response, endpoint)
        except RequestException as e:
            error_msg = f"Request failed: {str(e)} [{endpoint}]"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def delete(self, endpoint: str) -> dict[str, Any]:
        """Make DELETE request to API.

        Args:
            endpoint: API endpoint

        Returns:
            Response JSON as dictionary (or empty if 204 No Content)

        Raises:
            ValueError: If request fails
        """
        url = f"{self.api_url}/api/v1{endpoint}"
        try:
            response = self.session.delete(url, timeout=10)
            response.raise_for_status()
            # Handle 204 No Content
            if response.status_code == 204:
                return {"status": "success"}
            return response.json()
        except requests.exceptions.HTTPError:
            return self._handle_error(response, endpoint)
        except RequestException as e:
            error_msg = f"Request failed: {str(e)} [{endpoint}]"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def close(self) -> None:
        """Close session and cleanup."""
        self.session.close()


# Global client instance
_client: MCPAPIClient | None = None


def get_client(api_url: str = "http://localhost:8000") -> MCPAPIClient:
    """Get or create global API client instance.

    Args:
        api_url: Base URL for API server

    Returns:
        MCPAPIClient instance
    """
    global _client
    if _client is None:
        _client = MCPAPIClient(api_url)
    return _client


def set_client_token(token: str) -> None:
    """Set token for global client instance.

    Args:
        token: JWT token string
    """
    client = get_client()
    client.set_token(token)
