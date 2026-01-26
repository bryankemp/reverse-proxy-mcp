"""MCP resources for exposing proxy configuration data.

Resources provide read-only access to the reverse proxy configuration.
Each resource URI follows the proxy:// scheme with optional parameters.
"""

import json
import logging

from mcp.server.fastmcp import FastMCP

from reverse_proxy_mcp.mcp.client import get_client

logger = logging.getLogger(__name__)

# FastMCP instance will be imported from server.py
mcp: FastMCP = None  # type: ignore


def register_resources(mcp_instance: FastMCP) -> None:
    """Register all MCP resources with the FastMCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register resources with
    """
    global mcp
    mcp = mcp_instance

    @mcp.resource("proxy://backends")
    def list_all_backends() -> str:
        """List all backend servers with full configuration.

        Returns:
            JSON array of backend servers
        """
        try:
            client = get_client()
            result = client.get("/backends", params={"limit": 1000})
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch backends resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://backends/{backend_id}")
    def get_backend_by_id(backend_id: str) -> str:
        """Get single backend server details.

        Args:
            backend_id: Backend server ID

        Returns:
            JSON object with backend details
        """
        try:
            client = get_client()
            result = client.get(f"/backends/{backend_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch backend {backend_id} resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://rules")
    def list_all_proxy_rules() -> str:
        """List all proxy rules with relationships.

        Returns:
            JSON array of proxy rules with backend and certificate info
        """
        try:
            client = get_client()
            result = client.get("/proxy-rules", params={"limit": 1000})
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch proxy rules resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://rules/{rule_id}")
    def get_proxy_rule_by_id(rule_id: str) -> str:
        """Get single proxy rule with full details.

        Args:
            rule_id: Proxy rule ID

        Returns:
            JSON object with rule details
        """
        try:
            client = get_client()
            result = client.get(f"/proxy-rules/{rule_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch proxy rule {rule_id} resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://certificates")
    def list_all_certificates() -> str:
        """List all SSL/TLS certificates with metadata.

        Returns:
            JSON array of certificates (name, domain, is_default, expires_at)
        """
        try:
            client = get_client()
            result = client.get("/certificates", params={"limit": 1000})
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch certificates resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://certificates/{cert_id}")
    def get_certificate_by_id(cert_id: str) -> str:
        """Get certificate details (without private key).

        Args:
            cert_id: Certificate ID

        Returns:
            JSON object with certificate details
        """
        try:
            client = get_client()
            result = client.get(f"/certificates/{cert_id}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch certificate {cert_id} resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://config")
    def get_current_config() -> str:
        """Get current Nginx configuration from database.

        Returns:
            JSON object with configuration settings
        """
        try:
            client = get_client()
            result = client.get("/config")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch config resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://metrics")
    def get_aggregate_metrics() -> str:
        """Get aggregate metrics summary.

        Returns:
            JSON object with metrics data (requests, response times, errors)
        """
        try:
            client = get_client()
            result = client.get("/metrics", params={"limit": 100})
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch metrics resource: {e}")
            return json.dumps({"error": str(e)})

    @mcp.resource("proxy://audit-logs")
    def get_recent_audit_logs() -> str:
        """Get recent audit log entries (admin only).

        Returns:
            JSON array of recent audit log entries
        """
        try:
            client = get_client()
            result = client.get("/audit-logs", params={"limit": 100})
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Failed to fetch audit logs resource: {e}")
            return json.dumps({"error": str(e)})
