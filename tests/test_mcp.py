"""Unit tests for MCP client, handlers, and server.

Tests MCP API client HTTP calls and tool handler execution.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from nginx_manager.mcp.client import MCPAPIClient, get_client, set_client_token
from nginx_manager.mcp.handlers import TOOL_HANDLERS, ToolHandlers
from nginx_manager.mcp.tools import TOOLS


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

    @patch("nginx_manager.mcp.client.requests.Session.get")
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

    @patch("nginx_manager.mcp.client.requests.Session.get")
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

    @patch("nginx_manager.mcp.client.requests.Session.post")
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

    @patch("nginx_manager.mcp.client.requests.Session.put")
    def test_put_request_success(self, mock_put):
        """Test successful PUT request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "updated"}
        mock_put.return_value = mock_response

        client = MCPAPIClient()
        result = client.put("/backends/1", data={"name": "updated"})

        assert result["name"] == "updated"

    @patch("nginx_manager.mcp.client.requests.Session.delete")
    def test_delete_request_success(self, mock_delete):
        """Test successful DELETE request."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        client = MCPAPIClient()
        result = client.delete("/backends/1")

        assert result == {"status": "success"}

    @patch("nginx_manager.mcp.client.requests.Session.get")
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

    @patch("nginx_manager.mcp.client.requests.Session.get")
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


class TestToolHandlers:
    """Tests for tool handler execution."""

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_list_backends_handler(self, mock_get_client):
        """Test list_backends handler."""
        mock_client = Mock()
        mock_client.get.return_value = [{"id": 1, "name": "backend-1"}]
        mock_get_client.return_value = mock_client

        result = ToolHandlers.list_backends()

        assert result["status"] == "success"
        assert isinstance(result["data"], list)

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_create_backend_handler(self, mock_get_client):
        """Test create_backend handler."""
        mock_client = Mock()
        mock_client.post.return_value = {"id": 1, "name": "new-backend"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.create_backend(name="new-backend", host="localhost", port=8080)

        assert result["status"] == "success"
        mock_client.post.assert_called_once()

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_update_backend_handler(self, mock_get_client):
        """Test update_backend handler."""
        mock_client = Mock()
        mock_client.put.return_value = {"id": 1, "name": "updated"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.update_backend(1, name="updated")

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_delete_backend_handler(self, mock_get_client):
        """Test delete_backend handler."""
        mock_client = Mock()
        mock_client.delete.return_value = {}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.delete_backend(1)

        assert result["status"] == "success"
        assert "deleted" in result["message"].lower()

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_get_backend_handler(self, mock_get_client):
        """Test get_backend handler."""
        mock_client = Mock()
        mock_client.get.return_value = {"id": 1, "name": "backend-1"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.get_backend(1)

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_list_proxy_rules_handler(self, mock_get_client):
        """Test list_proxy_rules handler."""
        mock_client = Mock()
        mock_client.get.return_value = [{"id": 1, "domain": "example.com"}]
        mock_get_client.return_value = mock_client

        result = ToolHandlers.list_proxy_rules()

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_create_proxy_rule_handler(self, mock_get_client):
        """Test create_proxy_rule handler."""
        mock_client = Mock()
        mock_client.post.return_value = {"id": 1, "domain": "example.com"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.create_proxy_rule(domain="example.com", backend_id=1)

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_reload_nginx_handler(self, mock_get_client):
        """Test reload_nginx handler."""
        mock_client = Mock()
        mock_client.post.return_value = {}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.reload_nginx()

        assert result["status"] == "success"
        assert "reload" in result["message"].lower()

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_list_certificates_handler(self, mock_get_client):
        """Test list_certificates handler."""
        mock_client = Mock()
        mock_client.get.return_value = [{"id": 1, "domain": "example.com"}]
        mock_get_client.return_value = mock_client

        result = ToolHandlers.list_certificates()

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_create_certificate_handler(self, mock_get_client):
        """Test create_certificate handler."""
        mock_client = Mock()
        mock_client.post.return_value = {"id": 1, "domain": "example.com"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.create_certificate(
            domain="example.com",
            cert_pem="-----BEGIN CERTIFICATE-----",
            key_pem="-----BEGIN PRIVATE KEY-----",
        )

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_delete_certificate_handler(self, mock_get_client):
        """Test delete_certificate handler."""
        mock_client = Mock()
        mock_client.delete.return_value = {}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.delete_certificate(1)

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_get_certificate_handler(self, mock_get_client):
        """Test get_certificate handler."""
        mock_client = Mock()
        mock_client.get.return_value = {"id": 1, "domain": "example.com"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.get_certificate(1)

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_list_users_handler(self, mock_get_client):
        """Test list_users handler."""
        mock_client = Mock()
        mock_client.get.return_value = [{"id": 1, "username": "admin"}]
        mock_get_client.return_value = mock_client

        result = ToolHandlers.list_users()

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_create_user_handler(self, mock_get_client):
        """Test create_user handler."""
        mock_client = Mock()
        mock_client.post.return_value = {"id": 1, "username": "newuser"}
        mock_get_client.return_value = mock_client
        result = ToolHandlers.create_user(
            username="newuser", password="secure_password_123"  # noqa: S106
        )
        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_get_config_handler(self, mock_get_client):
        """Test get_config handler."""
        mock_client = Mock()
        mock_client.get.return_value = {"max_connections": 1000}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.get_config()

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_update_config_handler(self, mock_get_client):
        """Test update_config handler."""
        mock_client = Mock()
        mock_client.put.return_value = {"max_connections": 2000}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.update_config(max_connections=2000)

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_get_health_handler(self, mock_get_client):
        """Test get_health handler."""
        mock_client = Mock()
        mock_client.get.return_value = {"status": "healthy"}
        mock_get_client.return_value = mock_client

        result = ToolHandlers.get_health()

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_get_metrics_handler(self, mock_get_client):
        """Test get_metrics handler."""
        mock_client = Mock()
        mock_client.get.return_value = [{"timestamp": "2024-01-01", "requests": 100}]
        mock_get_client.return_value = mock_client

        result = ToolHandlers.get_metrics()

        assert result["status"] == "success"

    @patch("nginx_manager.mcp.handlers.get_client")
    def test_handler_error_handling(self, mock_get_client):
        """Test handler error handling."""
        mock_client = Mock()
        mock_client.get.side_effect = ValueError("API error")
        mock_get_client.return_value = mock_client

        result = ToolHandlers.list_backends()

        assert result["status"] == "error"
        assert "message" in result


class TestToolHandlerMapping:
    """Tests for tool handler mapping."""

    def test_all_tools_have_handlers(self):
        """Test that all defined tools have corresponding handlers."""
        for tool_name in TOOLS.keys():
            assert tool_name in TOOL_HANDLERS, f"Missing handler for tool: {tool_name}"

    def test_handler_count(self):
        """Test that exactly 21 handlers are registered."""
        assert len(TOOL_HANDLERS) == 21

    def test_tools_count(self):
        """Test that exactly 21 tools are defined."""
        assert len(TOOLS) == 21

    def test_all_handlers_are_callable(self):
        """Test that all handlers are callable."""
        for handler in TOOL_HANDLERS.values():
            assert callable(handler)


class TestToolDefinitions:
    """Tests for tool definitions structure."""

    def test_backend_tools_present(self):
        """Test that all 5 backend tools are defined."""
        backend_tools = [
            "list_backends",
            "create_backend",
            "update_backend",
            "delete_backend",
            "get_backend",
        ]
        for tool in backend_tools:
            assert tool in TOOLS

    def test_proxy_rule_tools_present(self):
        """Test that all 6 proxy rule tools are defined."""
        proxy_tools = [
            "list_proxy_rules",
            "create_proxy_rule",
            "update_proxy_rule",
            "delete_proxy_rule",
            "get_proxy_rule",
            "reload_nginx",
        ]
        for tool in proxy_tools:
            assert tool in TOOLS

    def test_certificate_tools_present(self):
        """Test that all 4 certificate tools are defined."""
        cert_tools = [
            "list_certificates",
            "create_certificate",
            "delete_certificate",
            "get_certificate",
        ]
        for tool in cert_tools:
            assert tool in TOOLS

    def test_user_config_tools_present(self):
        """Test that all 4 user/config tools are defined."""
        user_tools = [
            "list_users",
            "create_user",
            "get_config",
            "update_config",
        ]
        for tool in user_tools:
            assert tool in TOOLS

    def test_monitoring_tools_present(self):
        """Test that all 2 monitoring tools are defined."""
        monitoring_tools = [
            "get_health",
            "get_metrics",
        ]
        for tool in monitoring_tools:
            assert tool in TOOLS

    def test_tool_has_name(self):
        """Test that all tools have a name field."""
        for tool_name, tool_def in TOOLS.items():
            assert "name" in tool_def
            assert tool_def["name"] == tool_name

    def test_tool_has_description(self):
        """Test that all tools have a description."""
        for _tool_name, tool_def in TOOLS.items():
            assert "description" in tool_def
            assert len(tool_def["description"]) > 0

    def test_tool_has_input_schema(self):
        """Test that all tools have inputSchema."""
        for _tool_name, tool_def in TOOLS.items():
            assert "inputSchema" in tool_def
            assert "type" in tool_def["inputSchema"]
