"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from reverse_proxy_mcp.api.main import create_app
from reverse_proxy_mcp.core.security import create_access_token, hash_password
from reverse_proxy_mcp.models.database import BackendServer, Base, ProxyRule, User


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db(db_engine):
    """Get test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_nginx_dir():
    """Create temporary directory for Nginx config during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nginx_dir = Path(tmpdir) / "nginx"
        nginx_dir.mkdir()
        backup_dir = nginx_dir / "backup"
        backup_dir.mkdir()
        config_path = nginx_dir / "nginx.conf"
        config_path.touch()
        yield {"config_path": str(config_path), "backup_dir": str(backup_dir)}


@pytest.fixture
def mock_nginx_generator(test_nginx_dir, monkeypatch):
    """Mock NginxConfigGenerator to use test directories."""
    from reverse_proxy_mcp.core.nginx import NginxConfigGenerator

    def mock_init(self, config_path=None, backup_dir=None):
        """Mock init that uses test directories."""
        self.config_path = config_path or test_nginx_dir["config_path"]
        self.backup_dir = backup_dir or test_nginx_dir["backup_dir"]
        os.makedirs(self.backup_dir, exist_ok=True)

    def mock_validate_config(self, config_content: str) -> tuple[bool, str]:
        """Mock nginx validation - always succeeds in tests."""
        return True, "Configuration valid (mocked)"

    def mock_reload_nginx(self) -> tuple[bool, str]:
        """Mock nginx reload - always succeeds in tests."""
        return True, "Nginx reloaded (mocked)"

    monkeypatch.setattr(NginxConfigGenerator, "__init__", mock_init)
    monkeypatch.setattr(NginxConfigGenerator, "validate_config", mock_validate_config)
    monkeypatch.setattr(NginxConfigGenerator, "reload_nginx", mock_reload_nginx)


@pytest.fixture
def client(db, mock_nginx_generator):
    """Create FastAPI test client."""
    from reverse_proxy_mcp.core.database import get_db

    app = create_app()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def admin_user(db):
    """Create test admin user."""
    user = User(
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123456"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def regular_user(db):
    """Create test regular user."""
    user = User(
        username="user",
        email="user@test.com",
        password_hash=hash_password("user123456"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Create JWT token for admin user."""
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture
def user_token(regular_user):
    """Create JWT token for regular user."""
    return create_access_token(data={"sub": str(regular_user.id)})


@pytest.fixture
def backend_server(db, admin_user):
    """Create test backend server."""
    backend = BackendServer(
        name="test-backend",
        ip="192.168.1.100",
        port=8080,
        service_description="Test backend server",
        is_active=True,
        created_by=admin_user.id,
    )
    db.add(backend)
    db.commit()
    db.refresh(backend)
    return backend


@pytest.fixture
def proxy_rule(db, admin_user, backend_server):
    """Create test proxy rule."""
    rule = ProxyRule(
        frontend_domain="test.example.com",
        backend_id=backend_server.id,
        access_control="public",
        ip_whitelist=None,
        is_active=True,
        created_by=admin_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_auth_headers(user_token):
    """Get authorization headers with user token."""
    return {"Authorization": f"Bearer {user_token}"}
