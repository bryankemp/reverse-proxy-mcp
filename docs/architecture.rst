Architecture
============

System Overview
---------------

Reverse Proxy MCP is a containerized Nginx reverse proxy management system that replaces manual configuration with a dynamic, database-driven approach.

Key Features
^^^^^^^^^^^^

- **REST API** (v1 hierarchical URIs) for complete proxy management
- **MCP Server** for AI/LLM integration via Model Context Protocol
- **Flutter WebUI** for centralized proxy administration
- **Dynamic Configuration** with hot-reload capability (no container restart required)
- **Role-Based Access Control** (Admin and User roles)
- **Audit Logging** for compliance and change tracking
- **Monitoring & Metrics** with real-time performance data
- **SQLite Database** for lightweight, robust configuration storage

Component Architecture
----------------------

Frontend Layer
^^^^^^^^^^^^^^

**Flutter WebUI** (port 8080)
  - Responsive management interface
  - Role-based visibility (admin vs user screens)
  - Real-time metrics dashboards
  - Certificate management interface

**OpenAPI Swagger Docs** (port 8000/docs)
  - Interactive API documentation
  - Schema validation
  - Try-it-now interface

API Layer
^^^^^^^^^

**FastAPI Application** (port 8000)

v1 Endpoints (Hierarchical URIs):
  - ``/api/v1/backends`` - Backend server CRUD
  - ``/api/v1/proxy-rules`` - Proxy rule CRUD
  - ``/api/v1/certificates`` - SSL certificate management
  - ``/api/v1/users`` - User management (admin only)
  - ``/api/v1/config`` - Global configuration
  - ``/api/v1/monitoring`` - Health and metrics

Authentication:
  - JWT tokens with 24-hour expiry
  - Bcrypt password hashing (10 rounds)
  - Token-based stateless auth

Authorization:
  - Role-based decorators (``@require_admin``, ``@require_user``)
  - Granular permissions per endpoint
  - API returns 403 for unauthorized access

MCP Layer
^^^^^^^^^

**FastMCP Server** (port 5000)
  - 22 tools for proxy management
  - 9 resources for read-only configuration access
  - 5 prompts for guided workflows
  - HTTP streamable transport
  - ``proxy://`` URI scheme for resources

Tool Categories:
  - Backend management (5 tools)
  - Proxy rules (6 tools)
  - Certificates (5 tools)
  - Users & Config (4 tools)
  - Monitoring (2 tools)

Proxy Layer
^^^^^^^^^^^

**Nginx** (ports 80/443)
  - Dynamically configured from database
  - Template-based config generation (Jinja2)
  - Atomic reload with validation and rollback
  - SSL/TLS termination
  - Rate limiting and security headers

Data Layer
^^^^^^^^^^

**SQLite Database** (``./data/reverse_proxy_mcp.db``)

7 Tables:
  - ``users`` - User accounts with roles
  - ``backend_servers`` - Upstream backend definitions
  - ``proxy_rules`` - Domain-to-backend mappings
  - ``ssl_certificates`` - SSL/TLS certificates
  - ``audit_logs`` - Change tracking
  - ``proxy_config`` - Global settings
  - ``metrics`` - Performance data (30-day retention)

Features:
  - ACID transactions
  - Enforced referential integrity
  - Automatic timestamp tracking

Data Flow
---------

Configuration Change Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Configuration Change**: Admin creates/updates rule via WebUI → API endpoint
2. **Database Update**: API stores change in SQLite, logs in audit_logs table
3. **Config Generation**: API generates nginx.conf from database using Jinja2 template
4. **Validation**: ``nginx -t`` validates syntax, prevents reload if invalid
5. **Atomic Reload**: Backup old config → replace → send HUP signal → verify active
6. **Rollback**: If validation/reload fails, restore previous config and alert user

Request Flow
^^^^^^^^^^^^

1. Client request arrives at Nginx (port 80/443)
2. Nginx matches domain against server_name directives
3. SSL termination (if HTTPS)
4. Rate limiting applied (if configured)
5. IP whitelist check (if configured)
6. Proxy to backend server
7. Response returned to client
8. Metrics logged to database

User Roles
----------

Admin Role
^^^^^^^^^^

Permissions:
  - Full CRUD on all resources (backends, proxy rules, certificates, users)
  - Access to all screens in WebUI
  - Can view audit logs, modify configuration, reload Nginx
  - Cannot accidentally modify their own role (API prevents self-modification)

User Role
^^^^^^^^^

Permissions:
  - Read-only access to dashboards, metrics, certificate listings
  - Cannot see: user management, global configuration, audit logs, admin tools
  - Cannot see: edit/delete buttons on UI for protected resources
  - API returns 403 Forbidden if user attempts modification

Security Architecture
---------------------

Authentication
^^^^^^^^^^^^^^

- JWT tokens with 24-hour expiry
- Passwords hashed with bcrypt (10 rounds)
- Forced password change on first login for default admin
- Stateless token validation

Authorization
^^^^^^^^^^^^^

- Role-based access control at API layer
- Defense in depth (UI + API both check permissions)
- Granular endpoint-level protection
- Self-modification prevention (admin cannot change own role)

Data Security
^^^^^^^^^^^^^

- SQLAlchemy ORM prevents SQL injection
- Audit logging of all modifications
- No sensitive data in logs (passwords/tokens masked)
- Environment-based secrets management

Configuration Security
^^^^^^^^^^^^^^^^^^^^^^

- Validate syntax before reload
- Rollback on validation failure
- Never expose backend passwords in config
- Use environment variables for sensitive values

Network Security
^^^^^^^^^^^^^^^^

- SSL/TLS termination at Nginx
- HSTS support (HTTP Strict Transport Security)
- Rate limiting per domain
- IP whitelisting support
- Custom security headers

Deployment Architecture
-----------------------

Container Stack
^^^^^^^^^^^^^^^

Four containers via docker-compose:

1. **API Container** (Dockerfile.api)
   - FastAPI application
   - Database access
   - Configuration management

2. **MCP Container** (Dockerfile.mcp)
   - FastMCP server
   - Tool/resource/prompt handlers
   - API client wrapper

3. **WebUI Container** (Dockerfile.webui)
   - Flutter web build
   - Static file serving
   - SPA routing

4. **Nginx Container** (nginx/Dockerfile)
   - Nginx proxy
   - Dynamic configuration
   - SSL termination

Shared Resources:
  - SQLite database (volume mount)
  - Nginx configuration (volume mount)
  - SSL certificates (volume mount)

Scalability Considerations
^^^^^^^^^^^^^^^^^^^^^^^^^^

Current Design (Single Instance):
  - SQLite database (embedded)
  - Single Nginx instance
  - Single API/MCP instance
  - Suitable for small-to-medium deployments

Future Scalability:
  - Migrate to PostgreSQL/MySQL for horizontal scaling
  - Multiple Nginx instances with load balancer
  - API instance scaling with shared database
  - Distributed configuration synchronization
