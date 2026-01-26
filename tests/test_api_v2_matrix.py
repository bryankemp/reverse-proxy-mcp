"""Tests for API v2 matrix URI endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from reverse_proxy_mcp.models.database import BackendServer, ProxyRule, SSLCertificate, User


@pytest.mark.integration
class TestBackendMatrixEndpoints:
    """Test backend matrix endpoints."""

    def test_get_active_backends(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting only active backends."""
        # Create active and inactive backends
        active = BackendServer(
            name="active-backend",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        inactive = BackendServer(
            name="inactive-backend",
            ip="192.168.1.101",
            port=8081,
            protocol="http",
            is_active=False,
            created_by=admin_user.id,
        )
        db.add_all([active, inactive])
        db.commit()

        response = client.get(
            "/api/v2/active-backends", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "active-backend"

    def test_get_inactive_backends(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting only inactive backends."""
        inactive = BackendServer(
            name="inactive-backend",
            ip="192.168.1.101",
            port=8081,
            protocol="http",
            is_active=False,
            created_by=admin_user.id,
        )
        db.add(inactive)
        db.commit()

        response = client.get(
            "/api/v2/inactive-backends", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is False

    def test_get_backends_by_protocol(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting backends filtered by protocol."""
        http_backend = BackendServer(
            name="http-backend",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        https_backend = BackendServer(
            name="https-backend",
            ip="192.168.1.101",
            port=8443,
            protocol="https",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add_all([http_backend, https_backend])
        db.commit()

        response = client.get(
            "/api/v2/backends-by-protocol/http", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["protocol"] == "http"


@pytest.mark.integration
class TestProxyRuleMatrixEndpoints:
    """Test proxy rule matrix endpoints."""

    def test_get_public_rules(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting only public proxy rules."""
        backend = BackendServer(
            name="backend1",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add(backend)
        db.commit()

        public_rule = ProxyRule(
            frontend_domain="public.example.com",
            backend_id=backend.id,
            access_control="public",
            is_active=True,
            created_by=admin_user.id,
        )
        private_rule = ProxyRule(
            frontend_domain="private.example.com",
            backend_id=backend.id,
            access_control="private",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add_all([public_rule, private_rule])
        db.commit()

        response = client.get(
            "/api/v2/public-rules", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["access_control"] == "public"

    def test_get_private_rules(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting only private proxy rules."""
        backend = BackendServer(
            name="backend1",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add(backend)
        db.commit()

        private_rule = ProxyRule(
            frontend_domain="private.example.com",
            backend_id=backend.id,
            access_control="private",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add(private_rule)
        db.commit()

        response = client.get(
            "/api/v2/private-rules", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["access_control"] == "private"

    def test_get_ssl_enabled_rules(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting only SSL-enabled proxy rules."""
        backend = BackendServer(
            name="backend1",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add(backend)
        db.commit()

        ssl_rule = ProxyRule(
            frontend_domain="secure.example.com",
            backend_id=backend.id,
            ssl_enabled=True,
            is_active=True,
            created_by=admin_user.id,
        )
        db.add(ssl_rule)
        db.commit()

        response = client.get(
            "/api/v2/ssl-enabled-rules", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["ssl_enabled"] is True

    def test_get_rules_by_backend(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting rules for a specific backend."""
        backend1 = BackendServer(
            name="backend1",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        backend2 = BackendServer(
            name="backend2",
            ip="192.168.1.101",
            port=8081,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add_all([backend1, backend2])
        db.commit()

        rule1 = ProxyRule(
            frontend_domain="app1.example.com",
            backend_id=backend1.id,
            is_active=True,
            created_by=admin_user.id,
        )
        rule2 = ProxyRule(
            frontend_domain="app2.example.com",
            backend_id=backend1.id,
            is_active=True,
            created_by=admin_user.id,
        )
        rule3 = ProxyRule(
            frontend_domain="app3.example.com",
            backend_id=backend2.id,
            is_active=True,
            created_by=admin_user.id,
        )
        db.add_all([rule1, rule2, rule3])
        db.commit()

        response = client.get(
            f"/api/v2/rules-by-backend/{backend1.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(r["backend_id"] == backend1.id for r in data)

    def test_get_rules_by_certificate(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting rules using a specific certificate."""
        backend = BackendServer(
            name="backend1",
            ip="192.168.1.100",
            port=8080,
            protocol="http",
            is_active=True,
            created_by=admin_user.id,
        )
        db.add(backend)
        db.commit()

        cert = SSLCertificate(
            name="test-cert",
            domain="*.example.com",
            cert_path="/tmp/cert.pem",
            key_path="/tmp/key.pem",
            certificate_type="domain",
            expiry_date=datetime.now(UTC) + timedelta(days=365),
            is_default=False,
            uploaded_by=admin_user.id,
        )
        db.add(cert)
        db.commit()

        rule1 = ProxyRule(
            frontend_domain="app1.example.com",
            backend_id=backend.id,
            certificate_id=cert.id,
            is_active=True,
            created_by=admin_user.id,
        )
        rule2 = ProxyRule(
            frontend_domain="app2.example.com",
            backend_id=backend.id,
            is_active=True,
            created_by=admin_user.id,
        )
        db.add_all([rule1, rule2])
        db.commit()

        response = client.get(
            f"/api/v2/rules-by-certificate/{cert.id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["certificate_id"] == cert.id


@pytest.mark.integration
class TestCertificateMatrixEndpoints:
    """Test certificate matrix endpoints."""

    def test_get_expiring_certificates(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting expiring certificates."""
        # Certificate expiring in 20 days
        expiring_cert = SSLCertificate(
            name="expiring-cert",
            domain="expiring.example.com",
            cert_path="/tmp/cert.pem",
            key_path="/tmp/key.pem",
            certificate_type="domain",
            expiry_date=datetime.now(UTC) + timedelta(days=20),
            is_default=False,
            uploaded_by=admin_user.id,
        )
        # Certificate expiring in 100 days
        valid_cert = SSLCertificate(
            name="valid-cert",
            domain="valid.example.com",
            cert_path="/tmp/cert.pem",
            key_path="/tmp/key.pem",
            certificate_type="domain",
            expiry_date=datetime.now(UTC) + timedelta(days=100),
            is_default=False,
            uploaded_by=admin_user.id,
        )
        db.add_all([expiring_cert, valid_cert])
        db.commit()

        response = client.get(
            "/api/v2/expiring-certificates?days=30",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "expiring-cert"

    def test_get_default_certificates(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting default certificates."""
        default_cert = SSLCertificate(
            name="default-cert",
            domain="*.example.com",
            cert_path="/tmp/cert.pem",
            key_path="/tmp/key.pem",
            certificate_type="wildcard",
            expiry_date=datetime.now(UTC) + timedelta(days=365),
            is_default=True,
            uploaded_by=admin_user.id,
        )
        regular_cert = SSLCertificate(
            name="regular-cert",
            domain="app.example.com",
            cert_path="/tmp/cert.pem",
            key_path="/tmp/key.pem",
            certificate_type="domain",
            expiry_date=datetime.now(UTC) + timedelta(days=365),
            is_default=False,
            uploaded_by=admin_user.id,
        )
        db.add_all([default_cert, regular_cert])
        db.commit()

        response = client.get(
            "/api/v2/default-certificates", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_default"] is True


@pytest.mark.integration
class TestUserMatrixEndpoints:
    """Test user matrix endpoints."""

    def test_get_active_users(self, client: TestClient, user_token: str, db: Session):
        """Test getting only active users."""
        response = client.get(
            "/api/v2/active-users", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # At least admin user is active (regular_user fixture also active)
        assert len(data) >= 1
        assert all(u["is_active"] for u in data)

    def test_get_admin_users(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test getting only admin users."""
        response = client.get(
            "/api/v2/admin-users", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(u["role"] == "admin" for u in data)


@pytest.mark.integration
class TestMatrixAuthorizationV2:
    """Test authorization for matrix endpoints."""

    def test_requires_authentication(self, client: TestClient):
        """Test that matrix endpoints require authentication."""
        response = client.get("/api/v2/active-backends")

        assert response.status_code == 401

    def test_user_can_access_matrix_endpoints(self, client: TestClient, user_token: str):
        """Test that regular users can access matrix endpoints."""
        response = client.get(
            "/api/v2/active-backends", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestMatrixEdgeCases:
    """Test edge cases for matrix endpoints."""

    def test_expiring_certificates_with_custom_days(
        self, client: TestClient, user_token: str, db: Session, admin_user: User
    ):
        """Test expiring certificates with custom days parameter."""
        cert = SSLCertificate(
            name="cert1",
            domain="example.com",
            cert_path="/tmp/cert.pem",
            key_path="/tmp/key.pem",
            certificate_type="domain",
            expiry_date=datetime.now(UTC) + timedelta(days=50),
            is_default=False,
            uploaded_by=admin_user.id,
        )
        db.add(cert)
        db.commit()

        # Should find cert expiring in 50 days with days=60
        response = client.get(
            "/api/v2/expiring-certificates?days=60",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Should not find cert with days=40
        response = client.get(
            "/api/v2/expiring-certificates?days=40",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_empty_result_sets(self, client: TestClient, user_token: str):
        """Test matrix endpoints with empty result sets."""
        # No inactive backends
        response = client.get(
            "/api/v2/inactive-backends", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

        # No private rules
        response = client.get(
            "/api/v2/private-rules", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_rules_by_nonexistent_backend(self, client: TestClient, user_token: str):
        """Test getting rules for non-existent backend."""
        response = client.get(
            "/api/v2/rules-by-backend/999", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == 200
        assert response.json() == []
