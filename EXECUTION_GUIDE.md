# Nginx Manager - Execution Guide

## Project Status: 50% Complete (Phases 1-4.2 Done)

### Completed Work ✅
- Phase 1: Core API with SQLite, FastAPI auth, CRUD endpoints
- Phase 2: Certificate, user, audit management endpoints  
- Phase 3: Comprehensive test suite (42 tests, 75% coverage)
- Phase 4.1-4.2: MCP server scaffold, 21 tool definitions

### Current State
- 42 passing unit tests (75% code coverage)
- All code formatted (Black), linted (Ruff), type-checked (mypy)
- BSD 3-Clause license verified for all dependencies
- Architecture: Single-container deployment with Supervisord
- License: All dependencies compatible with BSD 3-Clause

## Remaining Implementation (4 Weeks)

### Phase 4: MCP Server Integration (Remaining: 3-4 days)
**Status**: Core setup complete, tools defined

1. **MCP API Client** (`src/nginx_manager/mcp/client.py`)
   - HTTP wrapper for calling REST API from tools
   - JWT token handling
   - Error handling and response parsing
   - ~150 lines

2. **MCP Tool Handlers** (`src/nginx_manager/mcp/handlers.py`)
   - Implement 21 tool execution handlers
   - Call API client for each tool
   - Log invocations via AuditService
   - ~300 lines

3. **MCP Server Integration** (Update `src/nginx_manager/api/main.py`)
   - Initialize MCP server on port 5000
   - Register all tools
   - Add MCP endpoints to FastAPI app
   - ~50 lines

4. **MCP Testing** (`tests/test_mcp.py`)
   - 15 unit tests for tool categories
   - Mock API responses
   - Authorization testing
   - ~250 lines

**Estimated effort**: 3-4 days  
**Success criteria**: All 21 tools accessible, 85%+ coverage

### Phase 5: Flutter WebUI (Remaining: 6-8 days)

This phase involves building a complete mobile/web UI in Flutter:

1. **Setup & Models** (1 day)
   - `webui/pubspec.yaml` with dependencies
   - Directory structure
   - Dart models for data

2. **Services & State Management** (1 day)
   - API service with error handling
   - Token storage service
   - Provider-based state management

3. **Authentication** (1 day)
   - Login screen
   - Token refresh
   - Session management

4. **CRUD Screens** (3 days)
   - 8 screens: Dashboard, Backends, Rules, Certificates, Users, Config, Audit, Settings
   - Role-based UI customization
   - List, detail, and form views

5. **Testing** (1 day)
   - Unit tests for models and providers
   - Screen integration tests
   - 70%+ coverage

**Estimated effort**: 6-8 days  
**Success criteria**: All screens working, role-based access enforced

### Phase 6: Documentation & Testing (Remaining: 3-4 days)

1. **Read the Docs Setup** (1 day)
   - Sphinx configuration
   - 10 documentation files
   - Architecture diagrams

2. **Integration Tests** (1 day)
   - 20+ test cases for complete workflows
   - Config generation tests
   - E2E validation

3. **Migration Scripts** (1 day)
   - Nginx config migration
   - Admin user initialization
   - Backup/restore scripts

**Estimated effort**: 3-4 days  
**Success criteria**: 80%+ coverage, docs deployed

### Phase 7: Single-Container Deployment (Remaining: 3-4 days)

1. **Unified Dockerfile** (1 day)
   - Alpine Linux + Python base
   - Install all dependencies
   - Supervisord configuration
   - Multi-process orchestration

2. **Docker Configuration** (1 day)
   - docker-compose.yml (optional, for convenience)
   - .env.example with all variables
   - Volume setup

3. **Deployment Scripts** (1 day)
   - deploy.sh - one-command deployment
   - upgrade.sh - rolling updates
   - Health check endpoints

4. **Production Hardening** (1 day)
   - Resource limits
   - Log rotation
   - Monitoring setup
   - SSL/TLS configuration

**Estimated effort**: 3-4 days  
**Success criteria**: Builds, starts, health checks pass

## Quick Start for Continuation

### Prerequisites
```bash
cd /Users/bryan/Projects/nginx-manager

# Ensure environment
python3 --version      # 3.11+
docker --version       # For final deployment
flutter --version      # For WebUI (optional, can skip if API-only)
```

### Development Setup
```bash
# Activate environment (if using venv)
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=src

# Code quality checks
black src tests
ruff check src tests
mypy src
```

### Phase 4 Implementation Order
1. Create `src/nginx_manager/mcp/client.py`
2. Create `src/nginx_manager/mcp/handlers.py`
3. Update `src/nginx_manager/api/main.py` to start MCP server
4. Create `tests/test_mcp.py`
5. Verify all tools callable: `curl http://localhost:5000/mcp`

### Phase 5 Implementation Order
1. Initialize Flutter: `flutter create webui`
2. Update `webui/pubspec.yaml`
3. Create directory structure
4. Implement services (API client, storage)
5. Implement providers (auth, data)
6. Build screens (dashboard first, then CRUD)
7. Add tests

### Phase 6 Implementation Order
1. Create `docs/` with Sphinx setup
2. Write 10 documentation files
3. Create `tests/test_integration.py` and `tests/test_e2e.py`
4. Create migration scripts in `scripts/`

### Phase 7 Implementation Order
1. Create unified `Dockerfile` with Supervisord
2. Create `supervisord.conf` for process management
3. Create `docker-compose.yml` (optional)
4. Create `.env.example`
5. Create `scripts/deploy.sh` and `scripts/upgrade.sh`
6. Create `nginx/entrypoint.sh`
7. Test: `docker build -t nginx-manager . && docker run -it -p 80:80 -p 8000:8000 nginx-manager`

## Key Architecture Decisions

### Single Container
- **Why**: Simplicity, resource efficiency, easier debugging
- **How**: Supervisord manages Nginx, FastAPI, and MCP in one container
- **Result**: ~200MB total, 5-10 second startup, one image to manage

### Integrated Services
- **Nginx**: Serves static WebUI, proxies API and MCP requests
- **FastAPI**: Runs on port 8000, provides REST API
- **MCP**: Runs on port 5000, provides AI tool interface
- **All**: Share same SQLite database, filesystem, process namespace

### Static WebUI
- Built from Flutter: `flutter build web`
- Served by Nginx from `/usr/share/nginx/html/`
- No Node.js, no complex build process
- ~5MB total size

## Testing Strategy

### Unit Tests (existing + new)
- API endpoints: ✅ Complete (16 tests)
- MCP tools: 🔄 In progress (target 15 tests)
- Flutter models/providers: ⬜ Pending (target 20 tests)

### Integration Tests (pending)
- Full workflows: `login → create backend → create rule → reload → verify`
- Config generation: Validate Nginx config syntax
- E2E: Test actual proxy behavior

### Coverage Targets
- Unit tests: 85%+ (all major code paths)
- Integration tests: 80%+ (full workflows)
- E2E tests: Key user scenarios

## Deployment Targets

### Development
```bash
docker run -d \
  -p 80:80 -p 443:443 \
  -p 8000:8000 -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=dev-key \
  nginx-manager:dev
```

### Production
```bash
docker run -d \
  --name nginx-manager \
  --restart unless-stopped \
  --memory=512m --cpus=0.5 \
  -p 80:80 -p 443:443 \
  -v /data:/app/data \
  -e SECRET_KEY=${SECRET_KEY} \
  -e DEBUG=false \
  nginx-manager:latest
```

## Success Criteria Checklist

- [ ] Phase 4: All 21 MCP tools implemented and tested (85%+ coverage)
- [ ] Phase 5: All 8 WebUI screens functional with role-based access (70%+ coverage)
- [ ] Phase 6: Documentation complete, 80%+ overall test coverage, integration tests pass
- [ ] Phase 7: Single Dockerfile builds, container starts, all health checks pass
- [ ] Final: All code quality checks pass (Black, Ruff, mypy)
- [ ] Final: Production deployment tested and documented

## Git Workflow

Each phase should result in a commit with clear message:
```bash
git add <files>
git commit -m "Phase X: Brief description

- Implementation detail 1
- Implementation detail 2
- Test coverage: X%+

Co-Authored-By: Warp <agent@warp.dev>"
```

## Estimated Timeline

- **Phase 4**: 3-4 days (MCP tools)
- **Phase 5**: 6-8 days (WebUI, can parallelize)
- **Phase 6**: 3-4 days (Docs & tests)
- **Phase 7**: 3-4 days (Containerization)
- **Buffer**: 2-3 days (testing, fixes)

**Total**: 4-5 weeks to production-ready

## Support Resources

- WARP.md: Development guidelines for phases 1-3
- ARCHITECTURE.md: Single-container design rationale
- DEPENDENCY_LICENSES.md: License compliance verification
- Tests: See tests/conftest.py for fixture patterns
- API: See src/nginx_manager/api/v1/ for endpoint patterns

## Next Immediate Action

Start with Phase 4.3: Create MCP API client wrapper and tool handlers.

This will enable testing all 21 tools via HTTP, which is needed before moving to Phase 5.
