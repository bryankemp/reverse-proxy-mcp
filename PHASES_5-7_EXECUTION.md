# Phases 5-7 Execution Guide

## Current Status
- **Phases 1-4**: Complete (API, MCP, 85 tests, 72% coverage)
- **Phase 5.1-5.3**: Complete (Flutter foundation, models, API/storage services)
- **Remaining**: Phase 5.4-5.12 (Providers, screens), Phase 6 (Docs, tests), Phase 7 (Docker)

## Phase 5 (Flutter WebUI) - Continued

### 5.4: Authentication Provider (Priority: CRITICAL)
**File**: `webui/lib/providers/auth_provider.dart`

```dart
// Key requirements:
class AuthProvider extends ChangeNotifier {
  final ApiService _apiService;
  final StorageService _storage;
  
  User? _currentUser;
  String? _token;
  bool _isLoading = false;
  String? _error;
  
  // Methods:
  Future<void> login(String email, String password, bool rememberMe);
  Future<void> logout();
  Future<void> autoLogin();  // Check stored token on app start
  Future<void> initializeStoredAuth();  // Initialize from storage
}
```

### 5.5: Data Providers (Priority: HIGH)
**Files**: 
- `webui/lib/providers/backend_provider.dart`
- `webui/lib/providers/rule_provider.dart`
- `webui/lib/providers/certificate_provider.dart`
- `webui/lib/providers/metrics_provider.dart`

All follow same pattern:
```dart
class BackendProvider extends ChangeNotifier {
  List<BackendServer> _backends = [];
  bool _isLoading = false;
  String? _error;
  
  // CRUD operations that notify listeners
  Future<void> fetchBackends();
  Future<void> createBackend(BackendServer backend);
  Future<void> updateBackend(BackendServer backend);
  Future<void> deleteBackend(int id);
}
```

### 5.6-5.10: UI Screens (Priority: HIGH)

**Screen Structure** (all follow this pattern):
```dart
// Each screen should:
// 1. Use Consumer<Provider> to rebuild on data changes
// 2. Handle loading, error, and empty states
// 3. Show role-based widgets (admin vs user)
// 4. Use ListView.builder for lists, cards for details
// 5. Include dialogs for forms

// Login Screen (5.6)
- Email and password TextFields
- Remember Me checkbox
- Login button with loading indicator
- Error message display
- Redirect to Dashboard on success

// Dashboard Screen (5.7)
- Status cards (# backends, # rules, # certs)
- Recent changes ListView
- Metrics chart (use fl_chart)
- Admin-only alerts panel

// CRUD Screens (5.8-5.10)
- List screens: DataTable or ListView with cards
- Detail screens: Card with info, Edit/Delete buttons
- Form screens: TextFields, DropdownButtons, validation
- Admin screens: Restricted to role check
```

### 5.11: Widgets & Navigation (Priority: MEDIUM)

**Essential Widgets**:
```dart
// app_drawer.dart - Navigation menu
// app_bar.dart - Custom AppBar with profile icon
// loading_indicator.dart - Center circular progress
// error_dialog.dart - Error message popup
// success_snackbar.dart - Confirmation message
// role_widget.dart - Show/hide by role
```

**Main Navigation**:
```dart
// webui/lib/main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final storage = await StorageService.initialize();
  final apiService = ApiService(storage);
  
  runApp(
    MultiProvider(
      providers: [
        Provider(create: (_) => storage),
        Provider(create: (_) => apiService),
        ChangeNotifierProvider(create: (_) => AuthProvider(apiService, storage)),
        ChangeNotifierProvider(create: (_) => BackendProvider(apiService)),
        // ... other providers
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Consumer<AuthProvider>(
        builder: (_, auth, __) => auth.isLoggedIn ? MainScreen() : LoginScreen(),
      ),
    );
  }
}
```

### 5.12: Testing (Priority: MEDIUM)

**Test Structure**:
```dart
// webui/test/providers/auth_provider_test.dart
// webui/test/services/api_service_test.dart
// webui/test/widgets/screens_test.dart

// Key tests:
- Login success/failure
- Auto-login from stored token
- Role-based visibility
- Provider state updates
- Form validation
- Error handling
```

**Run tests**:
```bash
cd webui && flutter test
```

---

## Phase 6 (Documentation & Integration Tests)

### 6.1-6.2: Sphinx Documentation

**Setup**:
```bash
cd /Users/bryan/Projects/nginx-manager
mkdir -p docs/_static docs/_templates
```

**Create** `docs/conf.py`:
```python
project = 'Nginx Manager'
extensions = ['myst_parser', 'sphinx_rtd_theme']
html_theme = 'sphinx_rtd_theme'
```

**Create** `docs/index.rst`:
```rst
Nginx Manager Documentation
===========================

.. toctree::
   installation
   architecture
   api-reference
   mcp-reference
   webui-guide
   deployment
   backup-restore
   troubleshooting
```

**Document files** (each 2-3 pages):
- `installation.rst`: Docker quick start, requirements
- `architecture.rst`: System design, data flow
- `api-reference.rst`: All endpoints with curl examples
- `mcp-reference.rst`: All 21 tools with schemas
- `webui-guide.rst`: Screenshots, workflows
- `deployment.rst`: Production setup, SSL
- `backup-restore.rst`: Database procedures
- `troubleshooting.rst`: Common issues

**Deploy to Read the Docs**:
1. Push to GitHub/GitLab
2. Enable on Read the Docs dashboard
3. Docs auto-build on push

### 6.3-6.4: Integration Tests

**File**: `tests/test_integration.py`

```python
# Key test scenarios:
def test_login_flow():
    # Login with user -> verify token -> redirect

def test_create_backend_workflow():
    # Login -> create backend -> verify in list -> update -> delete

def test_reload_config():
    # Create rule -> reload Nginx -> verify config generated

def test_metrics_collection():
    # Make requests -> check metrics -> verify counts

def test_role_based_access():
    # Admin sees all screens, user sees read-only

def test_audit_logging():
    # Perform action -> check audit log -> verify entry
```

**Run tests**:
```bash
uv run pytest tests/test_integration.py -v --cov
```

**Target**: 80%+ overall coverage, all green

### 6.5: Scripts

**migrate_from_nginx.py**:
- Parse existing `nginx.conf`
- Import servers and rules to database

**init_admin_user.py**:
- CLI to create initial admin user

**Backup/Restore Scripts**:
- Automated SQLite backup
- Restore from backup file

---

## Phase 7 (Containerization)

### 7.1-7.3: Single Dockerfile

**File**: `Dockerfile`

```dockerfile
# Stage 1: Flutter web build
FROM cirrusci/flutter:latest AS flutter_build
WORKDIR /app/webui
COPY webui/pubspec.* ./
COPY webui ./
RUN flutter pub get
RUN flutter build web --release

# Stage 2: Python app with Nginx
FROM python:3.11-alpine
RUN apk add --no-cache nginx supervisor
WORKDIR /app

# Copy Python app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install -e .[prod]

# Copy Flutter web output
COPY --from=flutter_build /app/webui/build/web /var/www/html

# Copy Nginx config
COPY nginx/nginx.conf.template /etc/nginx/
COPY nginx/entrypoint.sh /
RUN chmod +x /entrypoint.sh

# Copy Supervisord config
COPY supervisord.conf /etc/

EXPOSE 80 443
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost/health || exit 1
ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
```

### 7.2: supervisord.conf

```ini
[supervisord]
logfile=/var/log/supervisord.log

[program:nginx]
command=nginx -g "daemon off;"
stdout_logfile=/var/log/nginx_stdout.log
stderr_logfile=/var/log/nginx_stderr.log
autorestart=true

[program:fastapi]
command=uvicorn nginx_manager.api.main:create_app --host 0.0.0.0 --port 8000
directory=/app
stdout_logfile=/var/log/fastapi_stdout.log
stderr_logfile=/var/log/fastapi_stderr.log
autorestart=true

[program:mcp]
command=python -m nginx_manager.mcp
directory=/app
stdout_logfile=/var/log/mcp_stdout.log
stderr_logfile=/var/log/mcp_stderr.log
autorestart=true
```

### 7.3: entrypoint.sh

```bash
#!/bin/sh
set -e

# Initialize database
python -c "from nginx_manager.core import create_all_tables; create_all_tables()"

# Create admin user if not exists
python -c "
from nginx_manager.models.database import User
from nginx_manager.core.database import SessionLocal
admin_user = SessionLocal().query(User).filter_by(role='admin').first()
if not admin_user:
    # Create from env vars
    print('Creating admin user...')
"

# Setup Nginx config
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

exec "$@"
```

### 7.4-7.5: Docker Compose & .env

**File**: `docker-compose.yml`

```yaml
version: '3.8'
services:
  nginx-manager:
    build: .
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./data:/app/data
      - ./certs:/etc/nginx/certs
    environment:
      - DEBUG=false
      - DATABASE_URL=sqlite:///./data/nginx_manager.db
      - SECRET_KEY=${SECRET_KEY}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

**File**: `.env.example`

```env
DEBUG=false
SECRET_KEY=change-this-in-production
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme
CORS_ORIGINS=http://localhost:80,http://localhost:3000
LOG_LEVEL=INFO
```

### 7.6-7.8: Health Checks & Production

**Update** `src/nginx_manager/api/main.py`:

```python
@app.get("/health/ready")
async def health_ready() -> dict:
    """Kubernetes readiness probe"""
    return {
        "ready": True,
        "services": {
            "api": "running",
            "nginx": "running",
            "database": "connected"
        }
    }
```

**Production Setup**:
- Add SSL certificate paths to Nginx
- Enable log rotation
- Setup backup cron job
- Configure resource limits in Kubernetes/Docker

---

## Testing & Quality

### Before Each Phase Completion

```bash
# Python
uv run black src tests
uv run ruff check src tests
uv run mypy src
uv run pytest --cov

# Flutter (Phase 5)
cd webui
flutter analyze
flutter test
flutter build web --release --no-tree-shake-icons
```

### Final Validation

```bash
# Build Docker image
docker build -t nginx-manager:latest .

# Run with docker-compose
docker-compose up

# Test in browser: http://localhost
# - Login with admin credentials
# - Create backend
# - Create rule
# - Verify metrics
# - Check audit log
```

---

## Timeline

- **Phase 5**: 7-10 days (providers + 8 screens + widgets + tests)
- **Phase 6**: 5-7 days (docs + integration tests + scripts)
- **Phase 7**: 4-6 days (Docker + compose + hardening)
- **Total**: 3-4 weeks to production-ready

## Success Criteria

- ✅ Flutter app builds and runs without errors
- ✅ Login → Dashboard → CRUD workflows work end-to-end
- ✅ All 85 Python tests pass + new integration tests
- ✅ 80%+ overall test coverage
- ✅ Docker image builds and all services start
- ✅ Health checks pass
- ✅ Documentation deployed to Read the Docs
- ✅ All code quality checks (black, ruff, mypy) pass

## Next Steps

1. **Now**: Implement Phase 5.4 (AuthProvider)
2. **Then**: Build 8 screens in parallel (5.6-5.10)
3. **Parallel**: Write documentation as you go
4. **Then**: Build Docker during final week
5. **Final**: End-to-end testing and production hardening
