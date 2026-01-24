"""MCP tool definitions for Nginx Manager.

Defines 21 tools across 5 categories:
- Backend Management (5 tools)
- Proxy Rules (6 tools)
- Certificates (4 tools)
- Users & Configuration (4 tools)
- Monitoring (2 tools)
"""

from mcp.types import Tool


class ToolDefinitions:
    """MCP tool definitions for Nginx Manager."""

    # Backend Management Tools (5)
    LIST_BACKEND_SERVERS = Tool(
        name="list_backend_servers",
        description="List all backend servers (active and inactive)",
        inputSchema={
            "type": "object",
            "properties": {
                "active_only": {
                    "type": "boolean",
                    "description": "Filter to active backends only",
                },
            },
        },
    )

    GET_BACKEND_DETAILS = Tool(
        name="get_backend_details",
        description="Get detailed information about a specific backend server",
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Backend server ID",
                },
            },
            "required": ["server_id"],
        },
    )

    ADD_BACKEND_SERVER = Tool(
        name="add_backend_server",
        description="Create a new backend server (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Backend server name",
                },
                "ip": {
                    "type": "string",
                    "description": "IP address (IPv4 or IPv6)",
                },
                "port": {
                    "type": "integer",
                    "description": "Service port",
                },
                "description": {
                    "type": "string",
                    "description": "Optional service description",
                },
            },
            "required": ["name", "ip", "port"],
        },
    )

    UPDATE_BACKEND_SERVER = Tool(
        name="update_backend_server",
        description="Update an existing backend server (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Backend server ID",
                },
                "name": {"type": "string"},
                "ip": {"type": "string"},
                "port": {"type": "integer"},
                "description": {"type": "string"},
                "is_active": {
                    "type": "boolean",
                    "description": "Enable/disable backend",
                },
            },
            "required": ["server_id"],
        },
    )

    DELETE_BACKEND_SERVER = Tool(
        name="delete_backend_server",
        description="Delete a backend server (soft delete, admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "integer",
                    "description": "Backend server ID",
                },
            },
            "required": ["server_id"],
        },
    )

    # Proxy Rules Tools (6)
    LIST_PROXY_RULES = Tool(
        name="list_proxy_rules",
        description="List all proxy routing rules",
        inputSchema={
            "type": "object",
            "properties": {
                "active_only": {
                    "type": "boolean",
                    "description": "Filter to active rules only",
                },
            },
        },
    )

    GET_PROXY_RULE_DETAILS = Tool(
        name="get_proxy_rule_details",
        description="Get detailed information about a proxy rule",
        inputSchema={
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "integer",
                    "description": "Proxy rule ID",
                },
            },
            "required": ["rule_id"],
        },
    )

    CREATE_PROXY_RULE = Tool(
        name="create_proxy_rule",
        description="Create a new proxy rule (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "frontend_domain": {
                    "type": "string",
                    "description": "Frontend domain (e.g., example.com)",
                },
                "backend_id": {
                    "type": "integer",
                    "description": "Target backend server ID",
                },
                "access_control": {
                    "type": "string",
                    "enum": ["public", "internal"],
                    "description": "Access control type",
                },
                "ip_whitelist": {
                    "type": "string",
                    "description": "JSON array of allowed IPs (optional)",
                },
            },
            "required": ["frontend_domain", "backend_id"],
        },
    )

    UPDATE_PROXY_RULE = Tool(
        name="update_proxy_rule",
        description="Update an existing proxy rule (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "integer",
                    "description": "Proxy rule ID",
                },
                "frontend_domain": {"type": "string"},
                "backend_id": {"type": "integer"},
                "access_control": {
                    "type": "string",
                    "enum": ["public", "internal"],
                },
                "ip_whitelist": {"type": "string"},
                "is_active": {"type": "boolean"},
            },
            "required": ["rule_id"],
        },
    )

    DELETE_PROXY_RULE = Tool(
        name="delete_proxy_rule",
        description="Delete a proxy rule (soft delete, admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "rule_id": {
                    "type": "integer",
                    "description": "Proxy rule ID",
                },
            },
            "required": ["rule_id"],
        },
    )

    RELOAD_NGINX = Tool(
        name="reload_nginx",
        description="Hot reload Nginx configuration (admin only, no downtime)",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )

    # Certificate Tools (4)
    LIST_CERTIFICATES = Tool(
        name="list_certificates",
        description="List all SSL/TLS certificates",
        inputSchema={
            "type": "object",
            "properties": {
                "expiring_days": {
                    "type": "integer",
                    "description": "Optional: filter to certs expiring within N days",
                },
            },
        },
    )

    GET_CERTIFICATE_INFO = Tool(
        name="get_certificate_info",
        description="Get detailed information about a certificate",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Certificate domain",
                },
            },
            "required": ["domain"],
        },
    )

    UPLOAD_CERTIFICATE = Tool(
        name="upload_certificate",
        description="Upload a new SSL/TLS certificate (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Certificate domain",
                },
                "cert_pem": {
                    "type": "string",
                    "description": "Certificate in PEM format",
                },
                "key_pem": {
                    "type": "string",
                    "description": "Private key in PEM format",
                },
            },
            "required": ["domain", "cert_pem", "key_pem"],
        },
    )

    CHECK_CERTIFICATE_EXPIRY = Tool(
        name="check_certificate_expiry",
        description="Check SSL certificate expiry status",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Certificate domain",
                },
            },
            "required": ["domain"],
        },
    )

    # User & Configuration Tools (4)
    LIST_USERS = Tool(
        name="list_users",
        description="List all users (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "enum": ["admin", "user"],
                    "description": "Optional: filter by role",
                },
            },
        },
    )

    CREATE_USER = Tool(
        name="create_user",
        description="Create a new user (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Unique username",
                },
                "email": {
                    "type": "string",
                    "description": "User email address",
                },
                "password": {
                    "type": "string",
                    "description": "User password (minimum 8 characters)",
                },
                "role": {
                    "type": "string",
                    "enum": ["admin", "user"],
                    "description": "User role",
                },
            },
            "required": ["username", "email", "password", "role"],
        },
    )

    UPDATE_USER_ROLE = Tool(
        name="update_user_role",
        description="Update user role or status (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "User ID",
                },
                "role": {
                    "type": "string",
                    "enum": ["admin", "user"],
                    "description": "New role",
                },
                "is_active": {
                    "type": "boolean",
                    "description": "Enable/disable user",
                },
            },
            "required": ["user_id"],
        },
    )

    GET_PROXY_CONFIGURATION = Tool(
        name="get_proxy_configuration",
        description="Get global proxy configuration settings (admin only)",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )

    # Monitoring Tools (2)
    GET_PROXY_METRICS = Tool(
        name="get_proxy_metrics",
        description="Get current proxy metrics (requests, response times, errors)",
        inputSchema={
            "type": "object",
            "properties": {
                "backend_id": {
                    "type": "integer",
                    "description": "Optional: get metrics for specific backend",
                },
            },
        },
    )

    GET_AUDIT_LOGS = Tool(
        name="get_audit_logs",
        description="Get audit logs of system changes (admin only)",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of logs to return (default 100)",
                },
                "offset": {
                    "type": "integer",
                    "description": "Pagination offset (default 0)",
                },
                "user_id": {
                    "type": "integer",
                    "description": "Filter by user ID",
                },
                "action": {
                    "type": "string",
                    "description": "Filter by action (created, updated, deleted)",
                },
            },
        },
    )

    @staticmethod
    def get_all_tools() -> list[Tool]:
        """Get all 21 MCP tools.

        Returns:
            List of all Tool definitions
        """
        return [
            # Backend Management
            ToolDefinitions.LIST_BACKEND_SERVERS,
            ToolDefinitions.GET_BACKEND_DETAILS,
            ToolDefinitions.ADD_BACKEND_SERVER,
            ToolDefinitions.UPDATE_BACKEND_SERVER,
            ToolDefinitions.DELETE_BACKEND_SERVER,
            # Proxy Rules
            ToolDefinitions.LIST_PROXY_RULES,
            ToolDefinitions.GET_PROXY_RULE_DETAILS,
            ToolDefinitions.CREATE_PROXY_RULE,
            ToolDefinitions.UPDATE_PROXY_RULE,
            ToolDefinitions.DELETE_PROXY_RULE,
            ToolDefinitions.RELOAD_NGINX,
            # Certificates
            ToolDefinitions.LIST_CERTIFICATES,
            ToolDefinitions.GET_CERTIFICATE_INFO,
            ToolDefinitions.UPLOAD_CERTIFICATE,
            ToolDefinitions.CHECK_CERTIFICATE_EXPIRY,
            # Users & Configuration
            ToolDefinitions.LIST_USERS,
            ToolDefinitions.CREATE_USER,
            ToolDefinitions.UPDATE_USER_ROLE,
            ToolDefinitions.GET_PROXY_CONFIGURATION,
            # Monitoring
            ToolDefinitions.GET_PROXY_METRICS,
            ToolDefinitions.GET_AUDIT_LOGS,
        ]

    @staticmethod
    def get_tool_count() -> int:
        """Get total number of tools.

        Returns:
            21
        """
        return len(ToolDefinitions.get_all_tools())


# Export TOOLS dictionary for handler binding
TOOLS = {
    # Backend Management (5 tools)
    "list_backends": {
        "name": "list_backends",
        "description": "List all backend servers",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "create_backend": {
        "name": "create_backend",
        "description": "Create a new backend server",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "host": {"type": "string"},
                "port": {"type": "integer"},
                "protocol": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["name", "host", "port"],
        },
    },
    "update_backend": {
        "name": "update_backend",
        "description": "Update an existing backend server",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "delete_backend": {
        "name": "delete_backend",
        "description": "Delete a backend server",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_backend": {
        "name": "get_backend",
        "description": "Get backend details by ID",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # Proxy Rule Management (6 tools)
    "list_proxy_rules": {
        "name": "list_proxy_rules",
        "description": "List all proxy rules",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "create_proxy_rule": {
        "name": "create_proxy_rule",
        "description": "Create a new proxy rule",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "update_proxy_rule": {
        "name": "update_proxy_rule",
        "description": "Update an existing proxy rule",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "delete_proxy_rule": {
        "name": "delete_proxy_rule",
        "description": "Delete a proxy rule",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_proxy_rule": {
        "name": "get_proxy_rule",
        "description": "Get proxy rule details by ID",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "reload_nginx": {
        "name": "reload_nginx",
        "description": "Reload Nginx configuration without restarting",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # Certificate Management (4 tools)
    "list_certificates": {
        "name": "list_certificates",
        "description": "List all SSL/TLS certificates",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "create_certificate": {
        "name": "create_certificate",
        "description": "Upload a new SSL/TLS certificate",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "delete_certificate": {
        "name": "delete_certificate",
        "description": "Delete a certificate",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_certificate": {
        "name": "get_certificate",
        "description": "Get certificate details by ID",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # User & Configuration (4 tools)
    "list_users": {
        "name": "list_users",
        "description": "List all users (admin only)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "create_user": {
        "name": "create_user",
        "description": "Create a new user (admin only)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_config": {
        "name": "get_config",
        "description": "Get current system configuration",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "update_config": {
        "name": "update_config",
        "description": "Update system configuration (admin only)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    # Monitoring (2 tools)
    "get_health": {
        "name": "get_health",
        "description": "Get system health status",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "get_metrics": {
        "name": "get_metrics",
        "description": "Get system metrics",
        "inputSchema": {"type": "object", "properties": {}},
    },
}
