MCP Reference
=============

Model Context Protocol (MCP) Integration for AI/LLM Tools

The MCP server provides 22 tools, 9 resources, and 5 prompts for AI-powered proxy management.

Connection
----------

MCP Server Endpoint
^^^^^^^^^^^^^^^^^^^

The FastMCP server runs on port 5000::

    http://localhost:5000/mcp

Transport: HTTP Streamable

Configure AI Tool
^^^^^^^^^^^^^^^^^

Claude Desktop configuration (~/.claude/claude_desktop_config.json)::

    {
      "mcpServers": {
        "reverse-proxy": {
          "url": "http://localhost:5000/mcp",
          "transport": "http"
        }
      }
    }

Warp Agent Mode configuration::

    {
      "mcpServers": {
        "reverse-proxy": {
          "url": "http://localhost:5000/mcp",
          "transport": "http"
        }
      }
    }

Authentication
--------------

MCP tools require authentication. Set the admin JWT token::

    from reverse_proxy_mcp.mcp.client import set_client_token
    set_client_token("your_jwt_token_here")

MCP Tools (22)
--------------

Backend Management (5 tools)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

list_backends
"""""""""""""

List all backend servers.

Parameters:
- ``limit`` (int, default=50): Maximum results
- ``offset`` (int, default=0): Pagination offset

Returns: List of backend servers

create_backend
""""""""""""""

Create a new backend server.

Parameters:
- ``name`` (str): Unique backend name
- ``host`` (str): Hostname or IP address
- ``port`` (int): Port number (1-65535)
- ``protocol`` (str, default="http"): "http" or "https"
- ``description`` (str, default=""): Optional description

Returns: Created backend details

update_backend
""""""""""""""

Update an existing backend server.

Parameters:
- ``backend_id`` (int): Backend ID
- ``name`` (str, optional): New name
- ``host`` (str, optional): New host
- ``port`` (int, optional): New port
- ``protocol`` (str, optional): New protocol
- ``description`` (str, optional): New description

Returns: Updated backend details

delete_backend
""""""""""""""

Delete a backend server.

Parameters:
- ``backend_id`` (int): Backend ID

Returns: Deletion confirmation

get_backend
"""""""""""

Get backend details by ID.

Parameters:
- ``backend_id`` (int): Backend ID

Returns: Backend details

Proxy Rule Management (6 tools)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

list_proxy_rules
""""""""""""""""

List all proxy rules.

Parameters:
- ``limit`` (int, default=50): Maximum results
- ``offset`` (int, default=0): Pagination offset

Returns: List of proxy rules with backend and certificate info

create_proxy_rule
"""""""""""""""""

Create a new proxy rule.

Parameters:
- ``domain`` (str): Domain to match (e.g., "api.example.com")
- ``backend_id`` (int): Backend ID to proxy to
- ``path_pattern`` (str, default="/"): URL path pattern
- ``certificate_id`` (int, optional): SSL certificate ID
- ``rule_type`` (str, default="reverse_proxy"): Rule type

Returns: Created rule details

update_proxy_rule
"""""""""""""""""

Update an existing proxy rule.

Parameters:
- ``rule_id`` (int): Rule ID
- All create_proxy_rule parameters (optional)

Returns: Updated rule details

delete_proxy_rule
"""""""""""""""""

Delete a proxy rule.

Parameters:
- ``rule_id`` (int): Rule ID

Returns: Deletion confirmation

get_proxy_rule
""""""""""""""

Get proxy rule details by ID.

Parameters:
- ``rule_id`` (int): Rule ID

Returns: Rule details with backend and certificate info

reload_nginx
""""""""""""

Reload Nginx configuration.

Parameters: None

Returns: Reload status and message

Certificate Management (5 tools)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

list_certificates
"""""""""""""""""

List all SSL certificates.

Parameters:
- ``limit`` (int, default=50): Maximum results
- ``offset`` (int, default=0): Pagination offset

Returns: List of certificates (without private keys)

create_certificate
""""""""""""""""""

Upload a new SSL certificate.

Parameters:
- ``name`` (str): Friendly name
- ``domain`` (str): Domain pattern (e.g., "\*.example.com")
- ``cert_pem`` (str): PEM-encoded certificate
- ``key_pem`` (str): PEM-encoded private key
- ``is_default`` (bool, default=false): Set as default certificate
- ``description`` (str, default=""): Optional description

Returns: Created certificate details

get_certificate
"""""""""""""""

Get certificate details by ID.

Parameters:
- ``cert_id`` (int): Certificate ID

Returns: Certificate details (without private key)

set_default_certificate
"""""""""""""""""""""""

Set a certificate as the default.

Parameters:
- ``cert_id`` (int): Certificate ID

Returns: Updated certificate details

delete_certificate
""""""""""""""""""

Delete a certificate.

Parameters:
- ``cert_id`` (int): Certificate ID

Returns: Deletion confirmation

User & Configuration (4 tools)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

list_users
""""""""""

List all users (admin only).

Parameters:
- ``limit`` (int, default=50): Maximum results
- ``offset`` (int, default=0): Pagination offset

Returns: List of users

create_user
"""""""""""

Create a new user (admin only).

Parameters:
- ``username`` (str): Username
- ``password`` (str): Password (min 8 characters)
- ``role`` (str, default="user"): "admin" or "user"
- ``full_name`` (str, default=""): Full name

Returns: Created user details

get_config
""""""""""

Get system configuration.

Parameters: None

Returns: Configuration key-value pairs

update_config
"""""""""""""

Update system configuration (admin only).

Parameters:
- ``max_connections`` (int, optional): Max connections
- ``timeout_seconds`` (int, optional): Timeout in seconds

Returns: Updated configuration

Monitoring (2 tools)
^^^^^^^^^^^^^^^^^^^^

get_health
""""""""""

Get system health status.

Parameters: None

Returns: Health check with database, nginx status, active counts

get_metrics
"""""""""""

Get performance metrics.

Parameters:
- ``metric_type`` (str, default="requests"): Metric type
- ``limit`` (int, default=100): Maximum results

Returns: List of metric records

MCP Resources (9)
-----------------

Resources provide read-only access via ``proxy://`` URI scheme.

proxy://backends
^^^^^^^^^^^^^^^^

List all backend servers::

    [
        {
            "id": 1,
            "name": "my-app",
            "host": "192.168.1.10",
            "port": 3000,
            ...
        }
    ]

proxy://backends/{backend_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get single backend details by ID.

proxy://rules
^^^^^^^^^^^^^

List all proxy rules with relationships::

    [
        {
            "id": 1,
            "domain": "app.example.com",
            "backend_id": 1,
            "backend": {...},
            "certificate": {...}
        }
    ]

proxy://rules/{rule_id}
^^^^^^^^^^^^^^^^^^^^^^^

Get single proxy rule details by ID.

proxy://certificates
^^^^^^^^^^^^^^^^^^^^

List all SSL certificates::

    [
        {
            "id": 1,
            "name": "Wildcard Kempville",
            "domain": "*.kempville.com",
            "is_default": true,
            "expires_at": "2025-12-31T23:59:59"
        }
    ]

proxy://certificates/{cert_id}
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get single certificate details (without private key).

proxy://config
^^^^^^^^^^^^^^

Get current Nginx configuration from database.

proxy://metrics
^^^^^^^^^^^^^^^

Get aggregate metrics summary.

proxy://audit-logs
^^^^^^^^^^^^^^^^^^

Get recent audit log entries (admin only).

MCP Prompts (5)
---------------

Prompts provide guided workflows for common tasks.

setup_new_domain
^^^^^^^^^^^^^^^^

Complete domain setup workflow.

Parameters:
- ``domain`` (str): Domain name
- ``backend_host`` (str): Backend hostname
- ``backend_port`` (int): Backend port

Returns: Step-by-step setup instructions with tool calls

troubleshoot_proxy
^^^^^^^^^^^^^^^^^^

Diagnostic workflow for proxy issues.

Parameters:
- ``domain`` (str): Domain to troubleshoot

Returns: Diagnostic steps and relevant tools

configure_ssl
^^^^^^^^^^^^^

SSL certificate setup guide.

Parameters:
- ``domain`` (str): Domain name
- ``is_wildcard`` (bool, default=false): Whether domain is wildcard

Returns: Certificate generation and upload instructions

rotate_certificate
^^^^^^^^^^^^^^^^^^

Zero-downtime certificate rotation workflow.

Parameters:
- ``cert_id`` (int): Certificate ID to rotate

Returns: Rotation steps with affected proxy rules

create_user_account
^^^^^^^^^^^^^^^^^^^

User creation guide.

Parameters:
- ``username`` (str): Username
- ``role`` (str, default="user"): User role

Returns: User creation steps with security best practices

configure_wildcard_domain
^^^^^^^^^^^^^^^^^^^^^^^^^

Wildcard domain setup for multiple subdomains.

Parameters:
- ``base_domain`` (str): Base domain (e.g., "kempville.com")
- ``subdomains`` (list[str]): List of subdomains

Returns: Wildcard certificate and multi-rule setup guide

Example Usage
-------------

Using MCP with AI Assistant
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a backend and proxy rule::

    # Prompt
    setup_new_domain(
        domain="api.example.com",
        backend_host="10.0.0.5",
        backend_port=8080
    )
    
    # AI follows generated steps:
    # 1. create_backend(name="api-backend", host="10.0.0.5", port=8080)
    # 2. create_proxy_rule(domain="api.example.com", backend_id=1)
    # 3. reload_nginx()
    # 4. get_health()

Fetch configuration via resources::

    # Resource
    proxy://backends
    
    # Returns JSON array of all backends
    
    # Resource
    proxy://rules/1
    
    # Returns single rule with relationships

Troubleshoot a proxy issue::

    # Prompt
    troubleshoot_proxy(domain="broken.example.com")
    
    # AI uses resources and tools to diagnose:
    # - Checks proxy://rules for domain
    # - Checks proxy://backends for backend status
    # - Provides diagnostic steps
