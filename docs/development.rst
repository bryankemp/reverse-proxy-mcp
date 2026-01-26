Development Guide
=================

Development Environment
-----------------------

Requirements
^^^^^^^^^^^^

- Python 3.10 or higher
- uv (fast Python package manager)
- Docker & Docker Compose
- Flutter SDK (for WebUI development)
- Git

Installing Dependencies
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Clone repository
    git clone https://gitlab.kempville.com/yourusername/reverse-proxy-mcp.git
    cd reverse-proxy-mcp
    
    # Install Python dependencies
    uv sync --all-groups
    
    # Install pre-commit hooks
    pre-commit install

Running Locally
^^^^^^^^^^^^^^^

**API Server:**

.. code-block:: bash

    # Run with uv
    uv run python -m reverse_proxy_mcp
    
    # Or with uvicorn directly
    uv run uvicorn reverse_proxy_mcp.api.main:create_app --reload --port 8000

**MCP Server:**

.. code-block:: bash

    uv run python -m reverse_proxy_mcp.mcp

**Flutter WebUI:**

.. code-block:: bash

    cd webui
    flutter pub get
    flutter run -d chrome --web-port 8080

Code Quality Tools
------------------

Formatting
^^^^^^^^^^

**Black** (Python code formatter):

.. code-block:: bash

    # Format all Python code
    uv run python -m black src tests
    
    # Check without modifying
    uv run python -m black --check src tests

Configuration:
  - Line length: 100 characters
  - Target version: Python 3.10+
  - Config in ``pyproject.toml``

**Dart Formatter** (Flutter code):

.. code-block:: bash

    cd webui
    dart format lib/

Linting
^^^^^^^

**Ruff** (Python linter):

.. code-block:: bash

    # Lint all code
    uv run ruff check src tests
    
    # Auto-fix issues
    uv run ruff check --fix src tests

Configuration:
  - Line length: 100 characters
  - Rules: E, F, I, N, W, UP
  - Config in ``pyproject.toml``

Type Checking
^^^^^^^^^^^^^

**Mypy** (Python type checker):

.. code-block:: bash

    # Type check all source code
    uv run mypy src

Configuration:
  - Python version: 3.10
  - check_untyped_defs: true
  - no_implicit_optional: true
  - Config in ``pyproject.toml``

Running All Quality Checks
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Run all checks in sequence
    uv run python -m black src tests && \
    uv run ruff check src tests && \
    uv run mypy src

Testing
-------

Test Structure
^^^^^^^^^^^^^^

Tests are organized by category using pytest markers:

- **unit** (``pytest -m unit``): Fast, isolated tests with mocked dependencies
- **integration** (``pytest -m integration``): API endpoint tests with real database
- **e2e** (``pytest -m e2e``): Complete workflow tests with Nginx
- **docker** (``pytest -m docker``): Container integration tests

Running Tests
^^^^^^^^^^^^^

.. code-block:: bash

    # Run all tests
    uv run pytest
    
    # Run with coverage report
    uv run pytest --cov=src --cov-report=term-missing
    
    # Run specific category
    uv run pytest -m unit
    uv run pytest -m integration
    
    # Run specific test file
    uv run pytest tests/test_auth.py
    
    # Run specific test function
    uv run pytest tests/test_auth.py::test_login_success

Writing Tests
^^^^^^^^^^^^^

**Unit Test Example:**

.. code-block:: python

    import pytest
    from reverse_proxy_mcp.core.security import hash_password, verify_password
    
    @pytest.mark.unit
    def test_password_hashing():
        password = "test123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

**Integration Test Example:**

.. code-block:: python

    import pytest
    from fastapi.testclient import TestClient
    
    @pytest.mark.integration
    def test_create_backend(client: TestClient, admin_token: str):
        response = client.post(
            "/api/v1/backends",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "test-backend",
                "ip": "192.168.1.100",
                "port": 8080,
                "protocol": "http"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-backend"

Test Fixtures
^^^^^^^^^^^^^

Common fixtures defined in ``tests/conftest.py``:

- ``db``: In-memory SQLite database
- ``client``: FastAPI TestClient
- ``admin_user``: Test admin user object
- ``regular_user``: Test regular user object
- ``admin_token``: JWT token for admin user
- ``user_token``: JWT token for regular user
- ``mock_nginx_generator``: Mocked NginxConfigGenerator

Coverage Goals
^^^^^^^^^^^^^^

Target: **80%+ coverage** for production readiness

Current coverage areas:
  - Auth endpoints: ~90%
  - Backend/ProxyRule/Certificate services: ~85%
  - User service: ~80%
  - Monitoring endpoints: ~75%
  - Nginx config generation: ~70%

Low coverage areas (need improvement):
  - MCP tools/resources/prompts: ~30%
  - Error handling edge cases
  - Metrics aggregation

Project Structure
-----------------

.. code-block:: text

    reverse-proxy-mcp/
    ├── src/reverse_proxy_mcp/
    │   ├── __main__.py               # Entry point
    │   ├── api/
    │   │   ├── main.py               # FastAPI app factory
    │   │   ├── dependencies.py       # Auth dependencies
    │   │   └── v1/                   # API v1 endpoints
    │   │       ├── auth.py           # Authentication
    │   │       ├── backends.py       # Backend CRUD
    │   │       ├── proxy_rules.py    # Proxy rule CRUD
    │   │       ├── certificates.py   # Certificate management
    │   │       ├── users.py          # User management
    │   │       ├── config.py         # Configuration
    │   │       └── monitoring.py     # Health/metrics
    │   ├── core/
    │   │   ├── config.py             # Settings (pydantic-settings)
    │   │   ├── database.py           # SQLAlchemy setup
    │   │   ├── security.py           # JWT, bcrypt
    │   │   └── nginx.py              # Config generation
    │   ├── models/
    │   │   ├── database.py           # ORM models
    │   │   └── schemas.py            # Pydantic schemas
    │   ├── services/
    │   │   ├── backend.py
    │   │   ├── proxy_rule.py
    │   │   ├── certificate.py
    │   │   ├── user.py
    │   │   ├── audit.py
    │   │   └── metrics.py
    │   └── mcp/
    │       ├── __main__.py           # MCP entry point
    │       ├── server.py             # FastMCP server
    │       ├── tools.py              # 22 MCP tools
    │       ├── resources.py          # 9 MCP resources
    │       ├── prompts.py            # 5 MCP prompts
    │       └── client.py             # API client wrapper
    ├── webui/                        # Flutter web app
    │   ├── lib/
    │   │   ├── main.dart
    │   │   ├── models/models.dart
    │   │   ├── providers/
    │   │   ├── screens/
    │   │   ├── services/api_service.dart
    │   │   └── widgets/
    │   └── pubspec.yaml
    ├── tests/
    │   ├── conftest.py
    │   ├── test_auth.py
    │   ├── test_backends.py
    │   ├── test_certificates.py
    │   ├── test_monitoring.py
    │   ├── test_nginx.py
    │   └── test_integration.py
    ├── docs/                         # Sphinx documentation
    ├── nginx/
    │   ├── nginx.conf.template       # Jinja2 template
    │   └── Dockerfile
    ├── pyproject.toml
    └── docker-compose.yml

Adding New Features
-------------------

Adding an API Endpoint
^^^^^^^^^^^^^^^^^^^^^^

1. **Define Pydantic Schema** (``src/reverse_proxy_mcp/models/schemas.py``):

.. code-block:: python

    class MyResourceCreate(BaseModel):
        name: str
        value: int
    
    class MyResourceResponse(BaseModel):
        id: int
        name: str
        value: int
        created_at: datetime

2. **Define Database Model** (``src/reverse_proxy_mcp/models/database.py``):

.. code-block:: python

    class MyResource(Base):
        __tablename__ = "my_resources"
        
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        value = Column(Integer, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

3. **Create Service** (``src/reverse_proxy_mcp/services/my_resource.py``):

.. code-block:: python

    from sqlalchemy.orm import Session
    from reverse_proxy_mcp.models.database import MyResource
    
    class MyResourceService:
        @staticmethod
        def create(db: Session, name: str, value: int) -> MyResource:
            resource = MyResource(name=name, value=value)
            db.add(resource)
            db.commit()
            db.refresh(resource)
            return resource

4. **Create API Endpoint** (``src/reverse_proxy_mcp/api/v1/my_resource.py``):

.. code-block:: python

    from fastapi import APIRouter, Depends
    from sqlalchemy.orm import Session
    from reverse_proxy_mcp.api.dependencies import require_admin
    from reverse_proxy_mcp.core.database import get_db
    from reverse_proxy_mcp.models.schemas import MyResourceCreate, MyResourceResponse
    from reverse_proxy_mcp.services.my_resource import MyResourceService
    
    router = APIRouter(prefix="/api/v1/my-resources", tags=["my-resources"])
    
    @router.post("", response_model=MyResourceResponse, status_code=201)
    def create_resource(
        data: MyResourceCreate,
        db: Session = Depends(get_db),
        current_user = Depends(require_admin)
    ):
        resource = MyResourceService.create(db, data.name, data.value)
        return resource

5. **Register Router** (``src/reverse_proxy_mcp/api/main.py``):

.. code-block:: python

    from reverse_proxy_mcp.api.v1 import my_resource
    
    app.include_router(my_resource.router)

6. **Write Tests** (``tests/test_my_resource.py``):

.. code-block:: python

    import pytest
    
    @pytest.mark.integration
    def test_create_my_resource(client, admin_token):
        response = client.post(
            "/api/v1/my-resources",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "test", "value": 42}
        )
        assert response.status_code == 201

7. **Run Tests and Quality Checks:**

.. code-block:: bash

    uv run pytest tests/test_my_resource.py
    uv run black src tests
    uv run ruff check src tests
    uv run mypy src

Adding an MCP Tool
^^^^^^^^^^^^^^^^^^

1. **Define Tool** (``src/reverse_proxy_mcp/mcp/tools.py``):

.. code-block:: python

    from fastmcp import FastMCP
    
    def register_tools(mcp: FastMCP):
        @mcp.tool()
        def my_new_tool(param1: str, param2: int = 0) -> dict:
            """Brief description of what the tool does.
            
            Args:
                param1: Description of param1
                param2: Description of param2 (optional)
            
            Returns:
                Result dictionary with status and data/message
            """
            try:
                client = get_client()
                result = client.post("/api/v1/my-endpoint", json={
                    "param1": param1,
                    "param2": param2
                })
                return {"status": "success", "data": result}
            except Exception as e:
                logger.error(f"Tool failed: {e}")
                return {"status": "error", "message": str(e)}

2. **Test Tool Locally:**

.. code-block:: bash

    # Start API server
    uv run python -m reverse_proxy_mcp &
    
    # Start MCP server
    uv run python -m reverse_proxy_mcp.mcp
    
    # Test with MCP inspector
    pip install mcp-inspector
    mcp-inspector http://localhost:5000/mcp

3. **Write Tests** (``tests/test_mcp_tools.py``):

.. code-block:: python

    import pytest
    
    @pytest.mark.integration
    def test_my_new_tool():
        from reverse_proxy_mcp.mcp.tools import my_new_tool
        
        result = my_new_tool("value", 42)
        assert result["status"] == "success"

Adding a Flutter Screen
^^^^^^^^^^^^^^^^^^^^^^^

1. **Create Screen** (``webui/lib/screens/my_screen.dart``):

.. code-block:: dart

    import 'package:flutter/material.dart';
    import 'package:provider/provider.dart';
    
    class MyScreen extends StatefulWidget {
      @override
      _MyScreenState createState() => _MyScreenState();
    }
    
    class _MyScreenState extends State<MyScreen> {
      @override
      void initState() {
        super.initState();
        // Fetch data on load
        Future.microtask(() {
          context.read<MyProvider>().fetchData();
        });
      }
      
      @override
      Widget build(BuildContext context) {
        return Scaffold(
          appBar: AppBar(title: Text('My Screen')),
          body: Consumer<MyProvider>(
            builder: (context, provider, child) {
              if (provider.isLoading) {
                return Center(child: CircularProgressIndicator());
              }
              return ListView(children: [...]);
            },
          ),
        );
      }
    }

2. **Create Provider** (``webui/lib/providers/my_provider.dart``):

.. code-block:: dart

    import 'package:flutter/foundation.dart';
    import '../services/api_service.dart';
    
    class MyProvider with ChangeNotifier {
      final ApiService _apiService;
      List<MyModel> _items = [];
      bool _isLoading = false;
      
      MyProvider(this._apiService);
      
      List<MyModel> get items => _items;
      bool get isLoading => _isLoading;
      
      Future<void> fetchData() async {
        _isLoading = true;
        notifyListeners();
        
        try {
          _items = await _apiService.getMyItems();
        } catch (e) {
          print('Error: $e');
        } finally {
          _isLoading = false;
          notifyListeners();
        }
      }
    }

3. **Register Provider** (``webui/lib/main.dart``):

.. code-block:: dart

    providers: [
      ChangeNotifierProvider(create: (_) => MyProvider(apiService)),
    ]

4. **Add Route** (``webui/lib/main.dart``):

.. code-block:: dart

    GoRoute(
      path: '/my-screen',
      builder: (context, state) => MyScreen(),
    )

Database Migrations
-------------------

Creating a Migration Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For schema changes, create a migration script in ``scripts/``:

.. code-block:: python

    # scripts/migrate_add_new_column.py
    import sqlite3
    
    def migrate(db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Add new column
            cursor.execute("""
                ALTER TABLE my_table
                ADD COLUMN new_column TEXT DEFAULT ''
            """)
            
            conn.commit()
            print("Migration completed successfully")
        except Exception as e:
            conn.rollback()
            print(f"Migration failed: {e}")
        finally:
            conn.close()
    
    if __name__ == "__main__":
        migrate("./data/reverse_proxy_mcp.db")

Running Migrations
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Backup first
    cp ./data/reverse_proxy_mcp.db ./data/reverse_proxy_mcp.db.backup
    
    # Run migration
    uv run python scripts/migrate_add_new_column.py
    
    # Verify database
    sqlite3 ./data/reverse_proxy_mcp.db ".schema my_table"

Updating Test Fixtures
^^^^^^^^^^^^^^^^^^^^^^^

After schema changes, update ``tests/conftest.py`` fixtures:

.. code-block:: python

    @pytest.fixture
    def admin_user(db: Session) -> User:
        user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True,
            must_change_password=False,  # Add new field
            email="admin@test.com"
        )
        db.add(user)
        db.commit()
        return user

Git Workflow
------------

Branch Strategy
^^^^^^^^^^^^^^^

- ``main``: Production-ready code
- ``develop``: Integration branch for features
- ``feature/*``: Feature branches
- ``fix/*``: Bug fix branches

Creating a Feature Branch
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Start from develop
    git checkout develop
    git pull origin develop
    
    # Create feature branch
    git checkout -b feature/add-new-endpoint
    
    # Make changes, commit
    git add .
    git commit -m "feat(api): add new endpoint
    
    - Implement POST /api/v1/my-resource
    - Add tests for new endpoint
    - Update documentation
    
    Co-Authored-By: Warp <agent@warp.dev>"

Commit Message Format
^^^^^^^^^^^^^^^^^^^^^

Follow Conventional Commits:

.. code-block:: text

    type(scope): brief description
    
    Optional detailed explanation of changes.
    Can span multiple lines.
    
    Co-Authored-By: Warp <agent@warp.dev>

**Types:**
  - ``feat``: New feature
  - ``fix``: Bug fix
  - ``docs``: Documentation changes
  - ``style``: Code style (formatting, no logic change)
  - ``refactor``: Code restructuring (no behavior change)
  - ``test``: Add/update tests
  - ``chore``: Maintenance (dependencies, build config)
  - ``ci``: CI/CD changes

**Scopes:**
  - ``api``: REST API changes
  - ``mcp``: MCP server changes
  - ``webui``: Flutter WebUI changes
  - ``core``: Core utilities (security, database)
  - ``docs``: Documentation

Pre-Commit Checks
^^^^^^^^^^^^^^^^^

The pre-commit hook automatically runs:
  - Black formatting
  - Ruff linting
  - Mypy type checking
  - Pytest (unit tests only, for speed)

**Skip pre-commit** (not recommended):

.. code-block:: bash

    git commit --no-verify

Creating Pull Requests
^^^^^^^^^^^^^^^^^^^^^^

**Target:** ``develop`` branch (not ``main``)

**PR Title Format:**

- ``[Phase X] Description`` for planned work
- ``fix: Brief description`` for bug fixes
- ``feat: Brief description`` for features

**PR Checklist:**

.. code-block:: markdown

    - [ ] Tests passing (80%+ coverage)
    - [ ] Code quality checks passing (black, ruff, mypy)
    - [ ] Documentation updated
    - [ ] Database migrations included (if applicable)
    - [ ] Backwards compatible (or migration plan documented)
    - [ ] Co-authored by Warp

Docker Development
------------------

Building Containers
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Build all containers
    docker-compose build
    
    # Build specific service
    docker-compose build api

Running in Docker
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Start all services
    docker-compose up -d
    
    # View logs
    docker-compose logs -f api
    
    # Stop all services
    docker-compose down

Container Health Checks
^^^^^^^^^^^^^^^^^^^^^^^

All containers include health checks:

.. code-block:: yaml

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/monitoring/health"]
      interval: 30s
      timeout: 10s
      retries: 3

Debugging
---------

Enabling Debug Logging
^^^^^^^^^^^^^^^^^^^^^^

**API Server:**

.. code-block:: bash

    # Set log level in .env
    LOG_LEVEL=DEBUG
    
    # Restart API
    docker-compose restart api

**View Logs:**

.. code-block:: bash

    # API logs
    docker-compose logs -f api
    
    # Nginx logs
    docker-compose logs -f nginx
    
    # MCP logs
    docker-compose logs -f mcp

Interactive Debugging
^^^^^^^^^^^^^^^^^^^^^

**Using pdb:**

.. code-block:: python

    import pdb
    
    def my_function():
        pdb.set_trace()  # Breakpoint
        # Debug from here

**Using pytest with pdb:**

.. code-block:: bash

    # Drop into debugger on test failure
    uv run pytest --pdb

Database Inspection
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Connect to SQLite database
    sqlite3 ./data/reverse_proxy_mcp.db
    
    # List tables
    .tables
    
    # Describe table schema
    .schema users
    
    # Query data
    SELECT * FROM users;
    
    # Exit
    .quit

Testing Nginx Config
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Generate config from database
    docker-compose exec api python -c "
    from reverse_proxy_mcp.core.nginx import NginxConfigGenerator
    from reverse_proxy_mcp.core.database import SessionLocal
    
    db = SessionLocal()
    generator = NginxConfigGenerator(db)
    config = generator.generate_config()
    print(config)
    "
    
    # Validate config syntax
    docker-compose exec nginx nginx -t

Common Development Tasks
------------------------

Resetting Database
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Remove existing database
    rm ./data/reverse_proxy_mcp.db
    
    # Restart API (auto-initializes database)
    docker-compose restart api
    
    # Verify admin user created
    sqlite3 ./data/reverse_proxy_mcp.db "SELECT username, role FROM users;"

Updating Dependencies
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Update all dependencies
    uv sync --upgrade
    
    # Update specific package
    uv add fastapi@latest
    
    # Update Flutter dependencies
    cd webui
    flutter pub upgrade

Adding New Dependencies
^^^^^^^^^^^^^^^^^^^^^^^

**Python:**

.. code-block:: bash

    # Add to main dependencies
    uv add requests
    
    # Add to dev dependencies
    uv add --dev pytest-asyncio
    
    # Add to specific group
    uv add --group docs sphinx

**Flutter:**

.. code-block:: bash

    cd webui
    flutter pub add http
    flutter pub add --dev mockito

Regenerating OpenAPI Schema
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Start API server
    uv run python -m reverse_proxy_mcp &
    
    # Download OpenAPI schema
    curl http://localhost:8000/openapi.json > docs/openapi.json
    
    # View interactive docs
    open http://localhost:8000/docs

Performance Optimization
------------------------

Database Query Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Use eager loading** to avoid N+1 queries:

.. code-block:: python

    from sqlalchemy.orm import joinedload
    
    # Bad: N+1 query problem
    rules = db.query(ProxyRule).all()
    for rule in rules:
        print(rule.backend.name)  # Executes query per iteration
    
    # Good: Single query with join
    rules = db.query(ProxyRule).options(joinedload(ProxyRule.backend)).all()
    for rule in rules:
        print(rule.backend.name)  # No additional queries

**Add indexes** for frequently queried columns:

.. code-block:: python

    class MyResource(Base):
        __tablename__ = "my_resources"
        
        id = Column(Integer, primary_key=True)
        name = Column(String, index=True)  # Add index for search queries
        created_at = Column(DateTime, index=True)  # Index for sorting

API Response Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Use pagination** for large result sets:

.. code-block:: python

    @router.get("/resources")
    def list_resources(
        limit: int = 50,
        offset: int = 0,
        db: Session = Depends(get_db)
    ):
        items = db.query(MyResource).limit(limit).offset(offset).all()
        return items

**Cache expensive computations:**

.. code-block:: python

    from functools import lru_cache
    
    @lru_cache(maxsize=128)
    def get_expensive_data(key: str):
        # Cached for repeated calls with same key
        return compute_data(key)

Nginx Config Optimization
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Minimize config regeneration:**
  - Only regenerate when backends/rules/certificates change
  - Cache generated config in memory
  - Use atomic file operations to prevent partial writes

**Optimize reload:**
  - Use ``nginx -s reload`` (graceful) instead of restart
  - Validate config before reload to prevent downtime
  - Keep backup of last known good config

Security Considerations
-----------------------

JWT Token Security
^^^^^^^^^^^^^^^^^^

- Token expiry: 24 hours
- Algorithm: HS256
- Secret key: 32+ character random string in .env
- No token blacklist (stateless design)

Password Security
^^^^^^^^^^^^^^^^^

- Bcrypt hashing (10 rounds)
- Minimum 8 characters (enforced in Pydantic schema)
- Force password change on first login
- Old password required for changes (unless forced)

SQL Injection Prevention
^^^^^^^^^^^^^^^^^^^^^^^^^

- **Always use SQLAlchemy ORM** (parameterized queries)
- Never construct raw SQL with string interpolation
- Validate input with Pydantic schemas

Secrets Management
^^^^^^^^^^^^^^^^^^

- Store secrets in .env file (gitignored)
- Use environment variables in production
- Never commit secrets to repository
- Rotate SECRET_KEY periodically

CORS Configuration
^^^^^^^^^^^^^^^^^^

Restrict origins in ``src/reverse_proxy_mcp/api/main.py``:

.. code-block:: python

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],  # WebUI only
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

Deployment
----------

Production Checklist
^^^^^^^^^^^^^^^^^^^^

Before deploying:

1. Change default admin password
2. Set strong SECRET_KEY in .env
3. Update CORS allowed origins
4. Enable rate limiting
5. Configure SSL certificates
6. Set up database backups
7. Review audit log retention
8. Test health checks
9. Verify all tests pass
10. Run security audit

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

Required in production ``.env``:

.. code-block:: bash

    # Database
    DATABASE_URL=sqlite:///./data/reverse_proxy_mcp.db
    
    # Security
    SECRET_KEY=<64-character-random-string>
    JWT_EXPIRY_HOURS=24
    
    # Logging
    LOG_LEVEL=INFO
    
    # Admin (change these!)
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=<strong-password>
    ADMIN_EMAIL=admin@yourdomain.com

Docker Compose Production
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Build images
    docker-compose build
    
    # Start in detached mode
    docker-compose up -d
    
    # Verify health
    curl http://localhost:8000/api/v1/monitoring/health
    
    # View logs
    docker-compose logs -f

Monitoring Production
^^^^^^^^^^^^^^^^^^^^^

**Health Check:**

.. code-block:: bash

    # Add to monitoring system (Prometheus, Datadog, etc.)
    curl http://localhost:8000/api/v1/monitoring/health

**Metrics Collection:**

Set up cron job to parse Nginx logs:

.. code-block:: bash

    # Every 5 minutes
    */5 * * * * curl -X POST http://localhost:8000/api/v1/monitoring/parse-logs

**Log Aggregation:**

- Forward Nginx access logs to monitoring system
- Forward API logs to centralized logging (Splunk, ELK)

Troubleshooting Development Issues
-----------------------------------

Import Errors
^^^^^^^^^^^^^

.. code-block:: bash

    # Reinstall dependencies
    uv sync --reinstall
    
    # Clear cache
    uv cache clean

Database Lock Issues
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Check for stale processes
    lsof ./data/reverse_proxy_mcp.db
    
    # Kill stale processes
    kill <PID>

Port Already in Use
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Find process using port 8000
    lsof -i :8000
    
    # Kill process
    kill <PID>

Docker Build Failures
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Clean build cache
    docker-compose build --no-cache
    
    # Remove old containers/volumes
    docker-compose down -v

Contributing
------------

Code Review Guidelines
^^^^^^^^^^^^^^^^^^^^^^

When reviewing PRs:
  - Check test coverage (80%+ required)
  - Verify code quality checks pass
  - Review security implications
  - Test locally before approving
  - Ensure backwards compatibility

Documentation
^^^^^^^^^^^^^

Update documentation when:
  - Adding new API endpoints
  - Changing configuration options
  - Adding MCP tools
  - Modifying user workflows

Build docs locally:

.. code-block:: bash

    cd docs
    make html
    open _build/html/index.html

Issue Tracking
^^^^^^^^^^^^^^

Use GitLab issues for:
  - Bug reports
  - Feature requests
  - Documentation improvements
  - Performance issues

Label issues:
  - ``bug``: Something broken
  - ``enhancement``: New feature
  - ``docs``: Documentation
  - ``good-first-issue``: Good for new contributors

Resources
---------

- FastAPI Documentation: https://fastapi.tiangolo.com/
- FastMCP Documentation: https://github.com/jlowin/fastmcp
- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/14/orm/
- Flutter Documentation: https://flutter.dev/docs
- Nginx Documentation: https://nginx.org/en/docs/
- Model Context Protocol Spec: https://modelcontextprotocol.io/

Contact
-------

- Project maintainer: Bryan Kemp (bryan@kempville.com)
- Repository: https://gitlab.kempville.com/yourusername/reverse-proxy-mcp
- Issues: https://gitlab.kempville.com/yourusername/reverse-proxy-mcp/-/issues
