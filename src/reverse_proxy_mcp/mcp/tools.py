"""MCP tools for reverse proxy management using FastMCP decorators.

All 22 tools organized by category:
- Backend Management (5 tools)
- Proxy Rule Management (6 tools)
- Certificate Management (5 tools) - includes new set_default_certificate
- User & Configuration Management (4 tools)
- Monitoring (2 tools)
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from reverse_proxy_mcp.mcp.client import get_client

logger = logging.getLogger(__name__)

# FastMCP instance will be imported from server.py
mcp: FastMCP = None  # type: ignore


def register_tools(mcp_instance: FastMCP) -> None:
    """Register all MCP tools with the FastMCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    global mcp
    mcp = mcp_instance

    # ===== BACKEND MANAGEMENT (5 tools) =====

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
    def list_proxy_rules(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all proxy rules.

        Args:
            limit: Maximum number of results (default: 50)
            offset: Result offset for pagination (default: 0)

        Returns:
            List of proxy rules with backend and certificate information
        """
        try:
            client = get_client()
            result = client.get("/proxy-rules", params={"limit": limit, "offset": offset})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to list proxy rules: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def create_proxy_rule(
        domain: str,
        backend_id: int,
        path_pattern: str = "/",
        certificate_id: int | None = None,
        rule_type: str = "reverse_proxy",
    ) -> dict[str, Any]:
        """Create a new proxy rule.

        Args:
            domain: Domain to match (e.g., api.example.com)
            backend_id: Backend ID to proxy to
            path_pattern: URL path pattern (default: /)
            certificate_id: SSL certificate ID (optional)
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
            if certificate_id is not None:
                data["certificate_id"] = certificate_id

            result = client.post("/proxy-rules", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to create proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def update_proxy_rule(
        rule_id: int,
        domain: str | None = None,
        backend_id: int | None = None,
        path_pattern: str | None = None,
        certificate_id: int | None = None,
        rule_type: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing proxy rule.

        Args:
            rule_id: Proxy rule ID
            domain: New domain (optional)
            backend_id: New backend ID (optional)
            path_pattern: New path pattern (optional)
            certificate_id: New SSL certificate ID (optional, use -1 to remove)
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
            # Allow explicit None to be passed to remove certificate
            if certificate_id is not None:
                data["certificate_id"] = certificate_id if certificate_id != -1 else None

            result = client.put(f"/proxy-rules/{rule_id}", data=data)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to update proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
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

    @mcp.tool()
    def get_proxy_rule(rule_id: int) -> dict[str, Any]:
        """Get proxy rule details by ID.

        Args:
            rule_id: Proxy rule ID

        Returns:
            Rule details including backend and certificate information
        """
        try:
            client = get_client()
            result = client.get(f"/proxy-rules/{rule_id}")
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to get proxy rule: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
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

    # ===== CERTIFICATE MANAGEMENT (5 tools) =====

    @mcp.tool()
    def list_certificates(limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """List all SSL/TLS certificates.

        Args:
            limit: Maximum number of results (default: 50)
            offset: Result offset for pagination (default: 0)

        Returns:
            List of certificates with name, domain, is_default, expires_at
        """
        try:
            client = get_client()
            result = client.get("/certificates", params={"limit": limit, "offset": offset})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
    def create_certificate(
        name: str,
        domain: str,
        cert_pem: str,
        key_pem: str,
        is_default: bool = False,
        description: str = "",
    ) -> dict[str, Any]:
        """Upload a new SSL/TLS certificate.

        Args:
            name: Certificate name (unique, user-friendly identifier)
            domain: Certificate domain (supports wildcards like *.example.com)
            cert_pem: Certificate PEM content
            key_pem: Private key PEM content
            is_default: Set as default certificate (default: false)
            description: Certificate description

        Returns:
            Created certificate details
        """
        try:
            client = get_client()
            # Certificate upload uses multipart form data
            files = {
                "cert_file": ("cert.pem", cert_pem.encode(), "application/x-pem-file"),
                "key_file": ("key.pem", key_pem.encode(), "application/x-pem-file"),
            }
            data = {
                "name": name,
                "domain": domain,
                "is_default": "true" if is_default else "false",
                "description": description,
            }
            # Use multipart upload endpoint
            result = client.post("/certificates", data=data, files=files)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to create certificate: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
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

    @mcp.tool()
    def set_default_certificate(cert_id: int) -> dict[str, Any]:
        """Set a certificate as the default certificate.

        Args:
            cert_id: Certificate ID to set as default

        Returns:
            Updated certificate details
        """
        try:
            client = get_client()
            result = client.put(f"/certificates/{cert_id}/set-default", data={})
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Failed to set default certificate: {e}")
            return {"status": "error", "message": str(e)}

    @mcp.tool()
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

    # ===== USER & CONFIGURATION MANAGEMENT (4 tools) =====

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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

    @mcp.tool()
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
