# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Reverse Proxy MCP is a containerized Nginx reverse proxy management system that replaces manual configuration with a dynamic, database-driven approach. It provides:

- **REST API** (v1 hierarchical, v2 matrix URIs) for complete proxy management
- **MCP Server** for AI/LLM integration via Model Context Protocol
- **Flutter WebUI** for centralized proxy administration
- **Dynamic Configuration** with hot-reload capability (no container restart required)
- **Role-Based Access Control** (Admin and User roles with granular permissions)
- **Audit Logging** for compliance and change tracking
- **Monitoring & Metrics** with real-time performance data
- **SQLite Database** for lightweight, robust configuration storage

## Architecture

### Components

```
Frontend Layer:
- Flutter WebUI (port 8080) - Responsive management interface with role-based visibility
- OpenAPI Swagger Docs (port 8000/docs) - Interactive API documentation

API Layer:
- FastAPI application (port 8000)
  - v1 endpoints: Hierarchical resource-based URIs (/api/v1/backends, /api/v1/proxy-rules, etc.)
  - v2 endpoints: Matrix URIs for resource groups (/api/v2/active-backends, /api/v2/public-rules, etc.)
  - Authentication: JWT tokens (24-hour expiry)
  - Authorization: Role-based decorators (@require_admin, @require_user)

MCP Layer:
- FastMCP server (port 5000)
  - 21 tools for proxy management
  - Tool categories: Backend management, Proxy rules, Certificates, Users, Monitoring
  - Exposed via HTTP/SSE transport

Proxy Layer:
- Nginx (ports 80/443) - Dynamically configured from database
- Template-based config generation (Jinja2)
- Atomic reload with validation and rollback

Data Layer:
- SQLite database (./data/reverse_proxy_mcp.db)
  - 7 tables: users, backend_servers, proxy_rules, ssl_certificates, audit_logs, proxy_config, metrics
  - ACID transactions, enforced referential integrity
  - 30-day metrics retention (rolling window)
```

### Data Flow

1. **Configuration Change**: Admin creates/updates rule via WebUI → API endpoint
2. **Database Update**: API stores change in SQLite, logs in audit_logs table
3. **Config Generation**: API generates nginx.conf from database using Jinja2 template
4. **Validation**: nginx -t validates syntax, prevents reload if invalid
5. **Atomic Reload**: Backup old config → replace → send HUP signal → verify active
6. **Rollback**: If validation/reload fails, restore previous config and alert user

### User Roles

**Admin Role:**
- Full CRUD on all resources (backends, proxy rules, certificates, users)
- Access to all screens in WebUI
- Can view audit logs, modify configuration, reload Nginx
- Cannot accidentally modify their own role (API prevents self-modification)

**User Role:**
- Read-only access to dashboards, metrics, certificate listings
- Cannot see: user management, global configuration, audit logs, admin tools
- Cannot see: edit/delete buttons on UI for protected resources
- API returns 403 Forbidden if user attempts modification

## Development Commands

### Setup

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with uv (no venv needed, uv manages it)
uv sync --all-groups

# Install git hooks for automated quality checks
pre-commit install
```

### Running the Application

```bash
# Run API server locally with uv
uv run python -m reverse_proxy_mcp

# Or with uvicorn directly
uv run uvicorn reverse_proxy_mcp.api.main:create_app --reload --port 8000

# Run MCP server (after API is implemented)
uv run python -m reverse_proxy_mcp.mcp

# Run with docker-compose (after Dockerfiles are complete)
docker-compose up -d
```

### Code Quality (REQUIRED before commits)

```bash
# Format code with Black (line length: 100)
uv run python -m black src tests

# Lint with Ruff
uv run ruff check src tests

# Type check with mypy
uv run mypy src

# Run all checks together (pre-commit sequence)
uv run python -m black src tests && uv run ruff check src tests && uv run mypy src
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_auth.py

# Run specific test category
uv run pytest -m unit        # Unit tests only
uv run pytest -m integration # Integration tests only
uv run pytest -m e2e        # End-to-end tests

# Run only one test function
uv run pytest tests/test_auth.py::test_login_success
```

### Database

```bash
# Initialize database (automatic on app startup)
python -c "from reverse_proxy_mcp.core import create_all_tables; create_all_tables()"

# Create initial admin user (implement after user service)
python -m reverse_proxy_mcp.scripts.create_admin

# Database file location
./data/reverse_proxy_mcp.db
```

## Project Structure

```
reverse-proxy-mcp/
├── src/reverse_proxy_mcp/
│   ├── __init__.py
│   ├── __main__.py               # Entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app factory
│   │   ├── dependencies.py       # Auth dependencies
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py           # POST /login, /logout, /change-password
│   │       ├── backends.py       # GET/POST/PUT/DELETE /backends (admin only)
│   │       ├── proxy_rules.py    # GET/POST/PUT/DELETE /proxy-rules (admin only)
│   │       ├── certificates.py   # GET/POST/DELETE /certificates (admin only)
│   │       ├── users.py          # GET/POST/PUT/DELETE /users (admin only)
│   │       ├── config.py         # GET/PUT /config (admin only)
│   │       ├── audit_logs.py     # GET /audit-logs (admin only)
│   │       └── monitoring.py     # GET /metrics/*, /health
│   │   └── v2/
│   │       ├── __init__.py
│   │       └── matrix.py         # Matrix URI endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Settings from .env (pydantic-settings)
│   │   ├── database.py           # SQLAlchemy setup, session factory
│   │   ├── security.py           # JWT, bcrypt, password hashing
│   │   └── nginx.py              # Nginx config generation and reload
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py           # SQLAlchemy ORM models (7 tables)
│   │   └── schemas.py            # Pydantic request/response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── backend.py            # BackendServer business logic
│   │   ├── proxy_rule.py         # ProxyRule business logic
│   │   ├── certificate.py        # SSL certificate management
│   │   ├── user.py               # User management + role enforcement
│   │   ├── audit.py              # Audit logging service
│   │   └── metrics.py            # Metrics collection and aggregation
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py             # FastMCP server setup
│   │   └── tools.py              # 21 MCP tool definitions
│   └── migrations/               # Alembic (future: database versioning)
├── webui/                        # Flutter web project (minimal stub)
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures, mocks
│   ├── test_auth.py
│   ├── test_backends.py
│   ├── test_proxy_rules.py
│   ├── test_certificates.py
│   ├── test_users.py
│   ├── test_audit.py
│   └── test_integration.py
├── docs/                         # Read the Docs (future)
├── nginx/
│   ├── Dockerfile
│   ├── nginx.conf.template       # Jinja2 template for dynamic generation
│   └── entrypoint.sh
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.mcp
├── Dockerfile.webui
├── pyproject.toml                # Project metadata, dependencies, tool config
├── .env.example
├── .gitignore
├── README.md
└── WARP.md                       # This file
```

## Code Style & Patterns

### Black Configuration
- Line length: 100 characters
- Target: Python 3.10+
- Format command: `black src tests`

### Ruff Configuration
- Line length: 100 characters
- Selected rules: E, F, I, N, W, UP
- Target: Python 3.10+

### Mypy Configuration
- Python version: 3.10
- check_untyped_defs: true
- no_implicit_optional: true
- Ignore missing imports for external dependencies

### FastAPI Patterns

**Route protection with dependencies:**
```python
@router.get("/admin-only")
def admin_endpoint(current_user: User = Depends(require_admin)):
    # Only admins can access this
    return {"user_id": current_user.id}

@router.get("/user-info")
def user_endpoint(current_user: User = Depends(require_user)):
    # Any authenticated user can access
    return {"username": current_user.username}
```

**Database session management:**
```python
@router.get("/backends")
def list_backends(db: Session = Depends(get_db)):
    # Session automatically closed after response
    return db.query(BackendServer).all()
```

**Error handling pattern:**
```python
try:
    result = perform_operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Authorization Pattern

**Role enforcement in API:**
- Admin-only endpoints use `@require_admin` decorator
- Audit logging via service layer after successful operation
- Non-admin users cannot see edit/delete endpoints in responses
- API returns empty list or 403 for unauthorized access

**WebUI visibility:**
- Login endpoint returns user role in token
- Frontend conditionally renders admin screens based on role
- Hidden screens don't make API calls (no accidental exposure)
- All API endpoints double-check role (defense in depth)

## Database Schema Notes

### User Table
- `role`: 'admin' or 'user' (enforced in API)
- `is_active`: Boolean (can deactivate without deleting)
- `created_at`, `updated_at`: Audit timestamps

### BackendServer & ProxyRule Tables
- `created_by`: Foreign key to User (who created it)
- Unique constraints on name/domain to prevent duplicates
- `is_active`: Can disable rules without deletion

### AuditLog Table
- Triggered on every admin action (create, update, delete)
- `changes`: JSON string showing before/after values
- Indexed by timestamp for efficient queries
- 90-day retention policy (configurable)

### Metric Table
- Populated by parsing Nginx access logs every 5 minutes
- `backend_id`: NULL for aggregate metrics, FK for per-backend
- 30-day rolling retention (oldest entries auto-deleted)

## Git Workflow

### Repository Setup
```bash
# Clone from GitLab
git clone https://gitlab.kempville.com/yourusername/reverse-proxy-mcp.git
cd reverse-proxy-mcp

# Create develop branch
git checkout -b develop

# Set up initial feature branch
git checkout -b feature/complete-phase-1
```

### Commits

All commits must:
1. Follow conventional commits format: `type(scope): description`
   - Types: feat, fix, docs, style, refactor, test, chore, ci
   - Example: `feat(api): add backend server CRUD endpoints`

2. Include co-author attribution:
   ```
   git commit -m "feat(api): add backend server CRUD endpoints

   - POST /api/v1/backends to create backend
   - PUT /api/v1/backends/{id} to update
   - DELETE /api/v1/backends/{id} to remove

   Co-Authored-By: Warp <agent@warp.dev>"
   ```

3. Pass code quality checks before committing:
   ```bash
   black src tests && ruff check src tests && mypy src && pytest
   ```

### Pull Requests
- Target: `develop` branch (not main)
- Require passing CI/CD pipeline
- Require code review before merge
- Title format: `[Phase X] Description` or `fix: brief description`
- Include checklist:
  - [ ] Tests passing (80%+ coverage)
  - [ ] Code quality checks passing
  - [ ] Documentation updated
  - [ ] Database migrations included (if applicable)
  - [ ] Backwards compatible (or migration plan documented)

## Testing Architecture

### Test Categories (marked with @pytest.mark)

**Unit Tests** (`pytest -m unit`)
- Test individual functions/classes in isolation
- Mock external dependencies (database, HTTP calls)
- Fast execution (<5 seconds total)
- Example: Testing password hashing, JWT encoding

**Integration Tests** (`pytest -m integration`)
- Test API endpoints with real database
- Uses SQLite in-memory database for speed
- Creates/tears down test data
- Example: Test login endpoint → check user returned

**E2E Tests** (`pytest -m e2e`)
- Test complete workflows
- Creates actual Nginx config, validates syntax
- Takes longer (30+ seconds)
- Example: Create backend → Create rule → Verify config generated

**Docker Tests** (`pytest -m docker`)
- Build and run containers
- Test inter-service communication
- Verify health checks work
- Run: `pytest -m docker` (requires Docker)

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def db():
    """Provide in-memory SQLite database for tests."""
    # Create in-memory DB
    # Yield session
    # Teardown

@pytest.fixture
def client():
    """Provide TestClient for FastAPI app."""
    # Create app with test database
    # Yield client
    
@pytest.fixture
def admin_user(db):
    """Create test admin user."""
    # Create user with admin role
    # Return user object

@pytest.fixture
def regular_user(db):
    """Create test regular user."""
    # Create user with user role
    # Return user object

@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user."""
    # Create token
    # Return token string
```

## Security Considerations

### Secrets Management
- All secrets from environment variables (never hardcoded)
- .env file is gitignored (never committed)
- Production: Use GitLab CI/CD secrets
- Local development: Use .env created from .env.example

### API Security
- JWT tokens expire after 24 hours
- Passwords hashed with bcrypt (10 rounds)
- Rate limiting (implement: 100 requests/minute per IP)
- CSRF protection (implement with state tokens)
- CORS restricted to known origins

### Database Security
- SQLAlchemy ORM prevents SQL injection
- Role-based access control at API layer
- Audit logging of all modifications
- No sensitive data in logs (mask passwords, tokens)

### Nginx Config Security
- Validate syntax before reload
- Rollback on validation failure
- Never expose backend passwords in config
- Use environment variables for sensitive values

## Important Constraints

1. **Python 3.10+**: Uses modern type hints (e.g., `list[int]`, `dict | None`)
2. **SQLite Embedded**: No separate database server required
3. **Hot-reload Required**: Config changes must not restart container
4. **Role-based Visibility**: Non-admin users must not see admin features
5. **Audit Logging**: All admin actions logged with timestamp, user, IP
6. **Nginx Config Generation**: Must validate syntax, never deploy invalid config
7. **JWT Tokens**: Stateless (no blacklist needed), expires in 24 hours

## Development Roadmap

### Phase 1: Core API + Database ✅ (In Progress)
- SQLite schema (DONE)
- FastAPI scaffold (DONE)
- Auth endpoints (DONE)
- Backend CRUD endpoints (TODO)
- Proxy rule CRUD endpoints (TODO)
- Nginx config generation (TODO)

### Phase 2: Management Features (Next)
- Certificate management
- User management with role enforcement
- Configuration endpoints
- Audit logging

### Phase 3: Monitoring & Observability
- Nginx log parsing
- Metrics collection and storage
- Monitoring endpoints
- Health checks

### Phase 4: MCP Server
- Tool definitions (21 tools)
- API client wrapper
- Tool implementations

### Phase 5: Flutter WebUI
- Login/authentication
- Dashboard
- CRUD screens with role-based visibility
- Real-time metrics

### Phase 6: Documentation & Testing
- Read the Docs setup
- Comprehensive test suite
- Migration scripts
- Deployment guides

### Phase 7: Containerization & Deployment
- Dockerfiles for all components
- docker-compose orchestration
- Health checks and initialization
- CI/CD pipeline

## Related Documentation

- [Reverse Proxy MCP README](./README.md) - User-facing documentation
- [API Reference](./docs/api-reference.rst) - Endpoint documentation (TBD)
- [Architecture](./docs/architecture.rst) - Technical architecture (TBD)
- [Digital Loggers Power Switch Pro](https://www.digital-loggers.com/) - Original reverse proxy target

## Support & Questions

- Check WARP.md for development guidance
- Review existing code patterns before implementing new features
- Run tests before committing
- Use pre-commit hooks to catch issues early
- Email: bryan@kempville.com for questions
