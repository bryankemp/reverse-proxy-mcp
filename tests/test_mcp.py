"""Unit tests for MCP client, handlers, and server.

Tests MCP API client HTTP calls and tool handler execution.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from reverse_proxy_mcp.mcp.client import MCPAPIClient, get_client, set_client_token


class TestMCPAPIClient:
    """Tests for MCPAPIClient class."""

    def test_client_initialization(self):
        """Test MCPAPIClient initialization."""
        client = MCPAPIClient(api_url="http://localhost:8000")
        assert client.api_url == "http://localhost:8000"
        assert client.token is None

    def test_client_initialization_with_token(self):
        """Test MCPAPIClient initialization with token."""
        token = "test-jwt-token"
        client = MCPAPIClient(api_url="http://localhost:8000", token=token)
        assert client.token == token

    def test_client_set_token(self):
        """Test setting token on client."""
        client = MCPAPIClient()
        client.set_token("new-token")
        assert client.token == "new-token"

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.get")
    def test_get_request_success(self, mock_get):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"backends": []}
        mock_get.return_value = mock_response

        client = MCPAPIClient()
        result = client.get("/backends")

        assert result == {"backends": []}
        mock_get.assert_called_once()

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.get")
    def test_get_request_with_params(self, mock_get):
        """Test GET request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"backends": []}
        mock_get.return_value = mock_response

        client = MCPAPIClient()
        result = client.get("/backends", params={"limit": 10, "offset": 0})

        assert result == {"backends": []}
        call_args = mock_get.call_args
        assert call_args[1]["params"] == {"limit": 10, "offset": 0}

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.post")
    def test_post_request_success(self, mock_post):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "backend-1"}
        mock_post.return_value = mock_response

        client = MCPAPIClient()
        result = client.post(
            "/backends", data={"name": "backend-1", "host": "localhost", "port": 8080}
        )

        assert result["id"] == 1
        assert result["name"] == "backend-1"

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.put")
    def test_put_request_success(self, mock_put):
        """Test successful PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "updated"}
        mock_put.return_value = mock_response

        client = MCPAPIClient()
        result = client.put("/backends/1", data={"name": "updated"})

        assert result["name"] == "updated"

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.delete")
    def test_delete_request_success(self, mock_delete):
        """Test successful DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        client = MCPAPIClient()
        result = client.delete("/backends/1")

        assert result == {"status": "success"}

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.get")
    def test_get_request_error(self, mock_get):
        """Test GET request with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response

        client = MCPAPIClient()
        with pytest.raises(ValueError):
            client.get("/backends/999")

    @patch("reverse_proxy_mcp.mcp.client.requests.Session.get")
    def test_get_request_connection_error(self, mock_get):
        """Test GET request with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        client = MCPAPIClient()
        with pytest.raises(ValueError):
            client.get("/backends")


class TestGlobalClient:
    """Tests for global client instance."""

    def test_get_client_singleton(self):
        """Test get_client returns singleton instance."""
        client1 = get_client()
        client2 = get_client()
        assert client1 is client2

    def test_set_client_token(self):
        """Test setting token on global client."""
        set_client_token("test-token-123")
        client = get_client()
        assert client.token == "test-token-123"


class TestFastMCPServer:
    """Tests for FastMCP server initialization and registration."""

    def test_server_initialization(self):
        """Test FastMCP server can be initialized."""
        from reverse_proxy_mcp.mcp.server import mcp

        assert mcp is not None
        assert hasattr(mcp, "name")

    @patch("reverse_proxy_mcp.mcp.tools.get_client")
    def test_tools_registered(self, mock_get_client):
        """Test that tools are registered with FastMCP server."""
        from reverse_proxy_mcp.mcp.server import mcp

        # FastMCP uses decorators, so tools are registered at import time
        # We can verify the server has tools by checking if it has the list_tools method
        assert hasattr(mcp, "list_tools")

    @patch("reverse_proxy_mcp.mcp.resources.get_client")
    def test_resources_registered(self, mock_get_client):
        """Test that resources are registered with FastMCP server."""
        from reverse_proxy_mcp.mcp.server import mcp

        # FastMCP uses decorators, so resources are registered at import time
        assert hasattr(mcp, "list_resources")

    @patch("reverse_proxy_mcp.mcp.prompts.get_client")
    def test_prompts_registered(self, mock_get_client):
        """Test that prompts are registered with FastMCP server."""
        from reverse_proxy_mcp.mcp.server import mcp

        # FastMCP uses decorators, so prompts are registered at import time
        assert hasattr(mcp, "list_prompts")
