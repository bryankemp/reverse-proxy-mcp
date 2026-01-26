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
- 🔒 **SSL Management** - Upload and manage SSL certificates with expiry monitoring
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
docker-compose up -d

# Access the WebUI
# http://localhost:8080

# API documentation
# http://localhost:8000/docs
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

## API Documentation

- **REST API v1** (Hierarchical): `/api/v1/docs`
- **REST API v2** (Matrix): `/api/v2/docs`
- **MCP Tools**: See documentation for available tools

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
