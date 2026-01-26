# Reverse Proxy MCP

A containerized Nginx reverse proxy management system with REST API, Model Context Protocol (MCP) server, and Flutter WebUI. Provides centralized control, monitoring, and configuration for your reverse proxy infrastructure.

## Features

- 🔄 **Dynamic Configuration** - Hot-reload proxy rules without container restart
- 🌐 **REST API** - Hierarchical (v1) and matrix (v2) API endpoints for complete proxy management
- 🤖 **MCP Integration** - Control proxy via Model Context Protocol for AI/LLM compatibility
- 🎨 **Flutter WebUI** - Responsive web interface for proxy management
- 🔐 **Role-Based Access Control** - Admin and user roles with fine-grained permissions
- 📊 **Monitoring** - Real-time metrics, historical analytics, per-backend performance tracking
- 📝 **Audit Logging** - Complete change history and user activity tracking
- 🔒 **SSL Management** - Upload and manage SSL certificates with wildcard support, default certificates, and expiry monitoring
- 🐳 **Docker Ready** - Multi-container setup with docker-compose orchestration
- 📚 **Documentation** - Comprehensive Read the Docs documentation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx Proxy                             │
│              (Dynamically configured from DB)                │
└─────────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
    ┌────────┐          ┌─────────┐         ┌──────────┐
    │   API   │          │   MCP   │         │  WebUI   │
    │ (FastAPI)          │ (FastMCP)        │ (Flutter) │
    └────────┘          └─────────┘         └──────────┘
         ↓                    ↓                    ↓
    └─────────────────────────────────────────────────────────┘
              ↓
    ┌──────────────────────┐
    │   SQLite Database    │
    │                      │
    │ - Users              │
    │ - Backends           │
    │ - Proxy Rules        │
    │ - SSL Certificates   │
    │ - Audit Logs         │
    │ - Metrics            │
    └──────────────────────┘
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- `uv` package manager (recommended for fast installation)

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/yourusername/reverse-proxy-mcp.git
cd reverse-proxy-mcp

# Create environment configuration
cp .env.example .env

# Start all services
docker compose up -d

# Access the WebUI
# http://localhost (default credentials: admin / password)

# API documentation
# http://localhost:5100/docs
```

### Local Development

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with uv
uv sync --all-groups

# Set up pre-commit hooks
pre-commit install

# Run the API server
uv run python -m reverse_proxy_mcp

# Run tests
uv run pytest

# Run linting and type checking
uv run black src && uv run ruff check src && uv run mypy src
```

## Project Structure

```
reverse-proxy-mcp/
├── src/reverse_proxy_mcp/
│   ├── api/                    # FastAPI application
│   │   ├── v1/                 # REST API v1 endpoints
│   │   ├── v2/                 # REST API v2 endpoints
│   │   ├── dependencies.py     # FastAPI dependencies (auth, etc)
│   │   └── main.py             # API entry point
│   ├── mcp/                    # MCP server
│   │   ├── server.py           # MCP server implementation
│   │   └── tools.py            # MCP tool definitions
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database setup and sessions
│   │   ├── security.py         # Authentication and authorization
│   │   └── nginx.py            # Nginx config generation and reload
│   ├── models/
│   │   ├── database.py         # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── backend.py          # Backend server management
│   │   ├── proxy_rule.py       # Proxy rule management
│   │   ├── certificate.py      # SSL certificate management
│   │   ├── user.py             # User management
│   │   ├── audit.py            # Audit logging
│   │   └── metrics.py          # Metrics collection
│   └── migrations/             # Alembic database migrations
├── webui/                      # Flutter WebUI project
├── docker-compose.yml          # Multi-container orchestration
├── docs/                       # Read the Docs documentation
├── tests/                      # Test suite
├── Dockerfile.api              # API service Dockerfile
├── Dockerfile.mcp              # MCP server Dockerfile
└── nginx/
    ├── Dockerfile              # Nginx service Dockerfile
    └── nginx.conf.template     # Nginx configuration template
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./data/reverse_proxy_mcp.db

# JWT Configuration
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# MCP Configuration
MCP_HOST=0.0.0.0
MCP_PORT=5000

# Nginx Configuration
NGINX_CONFIG_PATH=/etc/nginx/sites-enabled/proxy.conf
NGINX_SOCKET_PATH=/var/run/nginx.sock
```

## SSL Certificate Management

Reverse Proxy MCP provides comprehensive SSL certificate management:

### Features

- **Named Certificates** - Assign friendly names to certificate pairs (e.g., "Wildcard Kempville", "API Certificate")
- **Wildcard Support** - Use wildcard certificates (*.example.com) across multiple subdomains
- **Default Certificate** - Set a default certificate for domains without explicit assignment
- **Certificate Assignment** - Assign specific certificates to individual proxy rules
- **Automatic Resolution** - Certificates are resolved in order:
  1. Explicit certificate assignment on proxy rule
  2. Exact domain match
  3. Wildcard domain match
  4. Default certificate fallback
- **Validation** - Certificate/key pair validation on upload
- **Expiry Monitoring** - Track certificate expiration and get alerts

### Certificate Upload

Using the API:

```bash
# Upload a wildcard certificate as default
curl -X POST http://localhost:5100/api/v1/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Wildcard Kempville" \
  -F "domain=*.kempville.com" \
  -F "is_default=true" \
  -F "cert_file=@/path/to/wildcard.crt" \
  -F "key_file=@/path/to/wildcard.key"

# Upload a domain-specific certificate
curl -X POST http://localhost:5100/api/v1/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=API Certificate" \
  -F "domain=api.example.com" \
  -F "is_default=false" \
  -F "cert_file=@/path/to/api.crt" \
  -F "key_file=@/path/to/api.key"
```

### Assigning Certificates to Proxy Rules

```bash
# Create proxy rule with explicit certificate
curl -X POST http://localhost:5100/api/v1/proxy-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frontend_domain": "api.kempville.com",
    "backend_id": 1,
    "certificate_id": 2
  }'

# Create proxy rule using default certificate (omit certificate_id)
curl -X POST http://localhost:5100/api/v1/proxy-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "frontend_domain": "app.kempville.com",
    "backend_id": 1
  }'
```

### List Available Certificates (for dropdowns)

```bash
curl -X GET http://localhost:5100/api/v1/certificates/dropdown \
  -H "Authorization: Bearer $TOKEN"
```

## MCP Server (Model Context Protocol)

Reverse Proxy MCP includes a FastMCP server for AI/LLM integration using the Anthropic Model Context Protocol specification.

### Features

- **22 Tools** - Complete proxy management via MCP tools
- **9 Resources** - Read-only access to configuration data via URI resources
- **5 Prompts** - Guided workflows for common tasks
- **HTTP Transport** - Standard streamable HTTP transport on port 5000

### Running the MCP Server

```bash
# Start MCP server locally
uv run python -m reverse_proxy_mcp.mcp

# MCP endpoint: http://localhost:5000/mcp
```

### Connecting AI Tools

Add to your AI tool configuration (e.g., Claude Desktop, Warp Agent Mode):

```json
{
  "mcpServers": {
    "reverse-proxy": {
      "url": "http://localhost:5000/mcp",
      "transport": "http"
    }
  }
}
```

### Available Tools

**Backend Management (5 tools)**
- `list_backends` - List all backend servers
- `create_backend` - Create new backend server
- `update_backend` - Update backend configuration
- `delete_backend` - Remove backend server
- `get_backend` - Get backend details by ID

**Proxy Rule Management (6 tools)**
- `list_proxy_rules` - List all proxy rules
- `create_proxy_rule` - Create new proxy rule (supports certificate_id)
- `update_proxy_rule` - Update proxy rule (supports certificate_id)
- `delete_proxy_rule` - Remove proxy rule
- `get_proxy_rule` - Get rule details by ID
- `reload_nginx` - Reload Nginx configuration

**Certificate Management (5 tools)**
- `list_certificates` - List all SSL certificates
- `create_certificate` - Upload certificate with name and is_default
- `get_certificate` - Get certificate details
- `set_default_certificate` - Set certificate as default
- `delete_certificate` - Remove certificate

**User & Configuration (4 tools)**
- `list_users` - List all users (admin only)
- `create_user` - Create new user (admin only)
- `get_config` - Get system configuration
- `update_config` - Update configuration (admin only)

**Monitoring (2 tools)**
- `get_health` - Get system health status
- `get_metrics` - Get performance metrics

### Available Resources

Resources provide read-only access to configuration data:

- `proxy://backends` - List all backends
- `proxy://backends/{backend_id}` - Single backend details
- `proxy://rules` - List all proxy rules
- `proxy://rules/{rule_id}` - Single rule details
- `proxy://certificates` - List all certificates
- `proxy://certificates/{cert_id}` - Single certificate details
- `proxy://config` - Current system configuration
- `proxy://metrics` - Aggregate metrics summary
- `proxy://audit-logs` - Recent audit log entries

### Available Prompts

Prompts provide guided workflows:

- `setup_new_domain(domain, backend_host, backend_port)` - Complete domain setup guide
- `troubleshoot_proxy(domain)` - Diagnostic steps for proxy issues
- `configure_ssl(domain, is_wildcard)` - SSL certificate setup guide
- `rotate_certificate(cert_id)` - Certificate rotation workflow
- `create_user_account(username, role)` - User creation guide
- `configure_wildcard_domain(base_domain, subdomains)` - Wildcard setup for multiple subdomains

### Example: Using MCP to Setup a New Domain

```python
# Via AI assistant with MCP access

# Use the setup_new_domain prompt
Prompt: setup_new_domain(
    domain="api.example.com",
    backend_host="10.0.0.5",
    backend_port=8080
)

# Follow the generated steps:
# 1. create_backend(name="api-example-com-backend", host="10.0.0.5", port=8080)
# 2. create_proxy_rule(domain="api.example.com", backend_id=1)
# 3. reload_nginx()
# 4. get_health()
```

### MCP Resources Example

```python
# Fetch all backends via resource
Resource: proxy://backends
# Returns JSON array of all backend servers

# Fetch specific backend
Resource: proxy://backends/1
# Returns single backend details

# Fetch all proxy rules
Resource: proxy://rules
# Returns rules with backend and certificate relationships
```

## API Documentation

- **REST API v1** (Hierarchical): `/api/v1/docs`
- **REST API v2** (Matrix): `/api/v2/docs`
- **MCP Endpoint**: `http://localhost:5000/mcp`

## Development Commands

Using `uv` (fast Python package manager):

```bash
# Format code
uv run black src

# Lint code
uv run ruff check src

# Type check
uv run mypy src

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_auth.py

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run only unit tests
uv run pytest -m unit

# Build Docker image
docker build -t reverse-proxy-mcp-api -f Dockerfile.api .

# Run Docker Compose
docker-compose up
```

## Testing

Run the full test suite:

```bash
pytest
```

Run specific test categories:

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# End-to-end tests
pytest -m e2e

# Docker container tests
pytest -m docker
```

## Documentation

Full documentation is available in the `docs/` directory and deployed to Read the Docs.

Key documentation files:
- `docs/installation.rst` - Setup instructions
- `docs/architecture.rst` - System architecture
- `docs/api-reference.rst` - Complete API endpoint documentation
- `docs/user-guide.rst` - WebUI usage guide
- `docs/administration.rst` - User management and permissions

## License

BSD 3-Clause License - See LICENSE file for details.

## Author

Bryan Kemp (bryan@kempville.com)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run code quality checks
5. Submit a pull request

## Support

- **Documentation**: https://reverse-proxy-mcp.readthedocs.io
- **Issues**: GitHub Issues
- **Email**: bryan@kempville.com
