"""MCP tool handlers implementing all 21 proxy management tools.

Each tool handler calls the REST API through the MCPAPIClient.
Follows the FastMCP tool definitions in tools.py.
"""

import logging
from typing import Any

from nginx_manager.mcp.client import get_client

logger = logging.getLogger(__name__)


class ToolHandlers:
    """All MCP tool handlers for proxy management."""

    # ===== BACKEND MANAGEMENT (5 tools) =====

    @staticmethod
    def list_backends(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all backend servers.

        Args:
            limit: Maximum number of results (default: 50)
            offset: Result offset for pagination (default: 0)

        Returns:
            List of backend servers
        """
        try:
            client = get_client()
            result = client.get("/backends", params={"limit": limit, "offset": offset})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to list backends: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_backend(
        name: str,
        host: str,
        port: int,
        protocol: str = "http",
        description: str = "",
    ) -> dict[str, Any]:
        """Create a new backend server.

        Args:
            name: Backend name (unique)
            host: Backend hostname or IP
            port: Backend port (1-65535)
            protocol: HTTP or HTTPS (default: http)
            description: Backend description

        Returns:
            Created backend details
        """
        try:
            client = get_client()
            data = {
                "name": name,
                "host": host,
                "port": port,
                "protocol": protocol,
                "description": description,
            }
            result = client.post("/backends", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to create backend: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def update_backend(
        backend_id: int,
        name: str | None = None,
        host: str | None = None,
        port: int | None = None,
        protocol: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing backend server.

        Args:
            backend_id: Backend ID
            name: New backend name (optional)
            host: New backend host (optional)
            port: New backend port (optional)
            protocol: New protocol (optional)
            description: New description (optional)

        Returns:
            Updated backend details
        """
        try:
            client = get_client()
            data = {}
            if name is not None:
                data["name"] = name
            if host is not None:
                data["host"] = host
            if port is not None:
                data["port"] = port
            if protocol is not None:
                data["protocol"] = protocol
            if description is not None:
                data["description"] = description

            result = client.put(f"/backends/{backend_id}", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to update backend: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def delete_backend(backend_id: int) -> dict[str, Any]:
        """Delete a backend server.

        Args:
            backend_id: Backend ID

        Returns:
            Deletion confirmation
        """
        try:
            client = get_client()
            client.delete(f"/backends/{backend_id}")
            return {"status": "success", "message": "Backend deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete backend: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_backend(backend_id: int) -> dict[str, Any]:
        """Get backend details by ID.

        Args:
            backend_id: Backend ID

        Returns:
            Backend details
        """
        try:
            client = get_client()
            result = client.get(f"/backends/{backend_id}")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get backend: {e}")
            return {"status": "error", "message": str(e)}

    # ===== PROXY RULE MANAGEMENT (6 tools) =====

    @staticmethod
    def list_proxy_rules(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all proxy rules.

        Args:
            limit: Maximum number of results (default: 50)
            offset: Result offset for pagination (default: 0)

        Returns:
            List of proxy rules
        """
        try:
            client = get_client()
            result = client.get("/proxy-rules", params={"limit": limit, "offset": offset})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to list proxy rules: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_proxy_rule(
        domain: str,
        backend_id: int,
        path_pattern: str = "/",
        rule_type: str = "reverse_proxy",
    ) -> dict[str, Any]:
        """Create a new proxy rule.

        Args:
            domain: Domain to match (e.g., api.example.com)
            backend_id: Backend ID to proxy to
            path_pattern: URL path pattern (default: /)
            rule_type: Rule type (default: reverse_proxy)

        Returns:
            Created rule details
        """
        try:
            client = get_client()
            data = {
                "domain": domain,
                "backend_id": backend_id,
                "path_pattern": path_pattern,
                "rule_type": rule_type,
            }
            result = client.post("/proxy-rules", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to create proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def update_proxy_rule(
        rule_id: int,
        domain: str | None = None,
        backend_id: int | None = None,
        path_pattern: str | None = None,
        rule_type: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing proxy rule.

        Args:
            rule_id: Proxy rule ID
            domain: New domain (optional)
            backend_id: New backend ID (optional)
            path_pattern: New path pattern (optional)
            rule_type: New rule type (optional)

        Returns:
            Updated rule details
        """
        try:
            client = get_client()
            data = {}
            if domain is not None:
                data["domain"] = domain
            if backend_id is not None:
                data["backend_id"] = backend_id
            if path_pattern is not None:
                data["path_pattern"] = path_pattern
            if rule_type is not None:
                data["rule_type"] = rule_type

            result = client.put(f"/proxy-rules/{rule_id}", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to update proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def delete_proxy_rule(rule_id: int) -> dict[str, Any]:
        """Delete a proxy rule.

        Args:
            rule_id: Proxy rule ID

        Returns:
            Deletion confirmation
        """
        try:
            client = get_client()
            client.delete(f"/proxy-rules/{rule_id}")
            return {"status": "success", "message": "Proxy rule deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_proxy_rule(rule_id: int) -> dict[str, Any]:
        """Get proxy rule details by ID.

        Args:
            rule_id: Proxy rule ID

        Returns:
            Rule details
        """
        try:
            client = get_client()
            result = client.get(f"/proxy-rules/{rule_id}")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def reload_nginx() -> dict[str, Any]:
        """Reload Nginx configuration without restarting.

        Returns:
            Reload status
        """
        try:
            client = get_client()
            client.post("/config/reload", data={})
            return {"status": "success", "message": "Nginx reloaded successfully"}
        except Exception as e:
            logger.error(f"Failed to reload Nginx: {e}")
            return {"status": "error", "message": str(e)}

    # ===== CERTIFICATE MANAGEMENT (4 tools) =====

    @staticmethod
    def list_certificates(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all SSL/TLS certificates.

        Args:
            limit: Maximum number of results (default: 50)
            offset: Result offset for pagination (default: 0)

        Returns:
            List of certificates
        """
        try:
            client = get_client()
            result = client.get("/certificates", params={"limit": limit, "offset": offset})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_certificate(
        domain: str, cert_pem: str, key_pem: str, description: str = ""
    ) -> dict[str, Any]:
        """Upload a new SSL/TLS certificate.

        Args:
            domain: Certificate domain
            cert_pem: Certificate PEM content
            key_pem: Private key PEM content
            description: Certificate description

        Returns:
            Created certificate details
        """
        try:
            client = get_client()
            data = {
                "domain": domain,
                "cert_pem": cert_pem,
                "key_pem": key_pem,
                "description": description,
            }
            result = client.post("/certificates", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def delete_certificate(cert_id: int) -> dict[str, Any]:
        """Delete a certificate.

        Args:
            cert_id: Certificate ID

        Returns:
            Deletion confirmation
        """
        try:
            client = get_client()
            client.delete(f"/certificates/{cert_id}")
            return {"status": "success", "message": "Certificate deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete certificate: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_certificate(cert_id: int) -> dict[str, Any]:
        """Get certificate details by ID.

        Args:
            cert_id: Certificate ID

        Returns:
            Certificate details (without private key)
        """
        try:
            client = get_client()
            result = client.get(f"/certificates/{cert_id}")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get certificate: {e}")
            return {"status": "error", "message": str(e)}

    # ===== USER & CONFIGURATION MANAGEMENT (4 tools) =====

    @staticmethod
    def list_users(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all users (admin only).

        Args:
            limit: Maximum number of results (default: 50)
            offset: Result offset for pagination (default: 0)

        Returns:
            List of users
        """
        try:
            client = get_client()
            result = client.get("/users", params={"limit": limit, "offset": offset})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_user(
        username: str, password: str, role: str = "user", full_name: str = ""
    ) -> dict[str, Any]:
        """Create a new user (admin only).

        Args:
            username: Username (unique)
            password: User password
            role: User role (admin or user, default: user)
            full_name: User full name

        Returns:
            Created user details (without password)
        """
        try:
            client = get_client()
            data = {
                "username": username,
                "password": password,
                "role": role,
                "full_name": full_name,
            }
            result = client.post("/users", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_config() -> dict[str, Any]:
        """Get current system configuration.

        Returns:
            Configuration details
        """
        try:
            client = get_client()
            result = client.get("/config")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def update_config(
        max_connections: int | None = None, timeout_seconds: int | None = None
    ) -> dict[str, Any]:
        """Update system configuration (admin only).

        Args:
            max_connections: Max connections (optional)
            timeout_seconds: Request timeout in seconds (optional)

        Returns:
            Updated configuration
        """
        try:
            client = get_client()
            data = {}
            if max_connections is not None:
                data["max_connections"] = max_connections
            if timeout_seconds is not None:
                data["timeout_seconds"] = timeout_seconds

            result = client.put("/config", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return {"status": "error", "message": str(e)}

    # ===== MONITORING (2 tools) =====

    @staticmethod
    def get_health() -> dict[str, Any]:
        """Get system health status.

        Returns:
            Health check details
        """
        try:
            client = get_client()
            result = client.get("/health")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get health: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_metrics(metric_type: str = "requests", limit: int = 100) -> dict[str, Any]:
        """Get system metrics (request count, response times, errors).

        Args:
            metric_type: Type of metrics (requests, response_time, errors)
            limit: Maximum number of data points

        Returns:
            Metrics data
        """
        try:
            client = get_client()
            result = client.get("/metrics", params={"metric_type": metric_type, "limit": limit})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"status": "error", "message": str(e)}


# Handler function mapping for tool execution
TOOL_HANDLERS = {
    # Backend management (5 tools)
    "list_backends": ToolHandlers.list_backends,
    "create_backend": ToolHandlers.create_backend,
    "update_backend": ToolHandlers.update_backend,
    "delete_backend": ToolHandlers.delete_backend,
    "get_backend": ToolHandlers.get_backend,
    # Proxy rule management (6 tools)
    "list_proxy_rules": ToolHandlers.list_proxy_rules,
    "create_proxy_rule": ToolHandlers.create_proxy_rule,
    "update_proxy_rule": ToolHandlers.update_proxy_rule,
    "delete_proxy_rule": ToolHandlers.delete_proxy_rule,
    "get_proxy_rule": ToolHandlers.get_proxy_rule,
    "reload_nginx": ToolHandlers.reload_nginx,
    # Certificate management (4 tools)
    "list_certificates": ToolHandlers.list_certificates,
    "create_certificate": ToolHandlers.create_certificate,
    "delete_certificate": ToolHandlers.delete_certificate,
    "get_certificate": ToolHandlers.get_certificate,
    # User & configuration (4 tools)
    "list_users": ToolHandlers.list_users,
    "create_user": ToolHandlers.create_user,
    "get_config": ToolHandlers.get_config,
    "update_config": ToolHandlers.update_config,
    # Monitoring (2 tools)
    "get_health": ToolHandlers.get_health,
    "get_metrics": ToolHandlers.get_metrics,
}
