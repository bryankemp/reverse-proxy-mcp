"""Unit tests for certificate and configuration endpoints."""

import pytest
from fastapi import status


@pytest.mark.unit
class TestCertificates:
    """Test certificate management endpoints."""

    def test_list_certificates(self, client, user_auth_headers):
        """Test listing certificates."""
        response = client.get("/api/v1/certificates", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        certs = response.json()
        assert isinstance(certs, list)

    def test_list_expiring_certificates(self, client, user_auth_headers):
        """Test listing expiring certificates."""
        response = client.get(
            "/api/v1/certificates/expiring/list?days=30",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "count" in data
        assert "certificates" in data

    def test_check_certificate_expiry_not_found(self, client, user_auth_headers):
        """Test checking expiry for nonexistent certificate."""
        response = client.get(
            "/api/v1/certificates/nonexistent.com/expiry-status",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
class TestConfiguration:
    """Test configuration endpoints."""

    def test_get_config_unauthorized(self, client, user_auth_headers):
        """Test getting config as regular user."""
        response = client.get("/api/v1/config", headers=user_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_config_admin(self, client, auth_headers):
        """Test getting config as admin."""
        response = client.get("/api/v1/config", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)

    def test_set_config_admin(self, client, auth_headers):
        """Test setting config value as admin."""
        response = client.put(
            "/api/v1/config/test_key?value=test_value",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["key"] == "test_key"
        assert data["value"] == "test_value"

    def test_set_config_unauthorized(self, client, user_auth_headers):
        """Test setting config as regular user."""
        response = client.put(
            "/api/v1/config/test_key?value=test_value",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_audit_logs_unauthorized(self, client, user_auth_headers):
        """Test listing audit logs as regular user."""
        response = client.get(
            "/api/v1/config/logs/all",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_audit_logs_admin(self, client, auth_headers):
        """Test listing audit logs as admin."""
        response = client.get(
            "/api/v1/config/logs/all",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        logs = response.json()
        assert isinstance(logs, list)

    def test_cleanup_audit_logs_unauthorized(self, client, user_auth_headers):
        """Test cleaning audit logs as regular user."""
        response = client.post(
            "/api/v1/config/logs/cleanup?days_retention=90",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cleanup_audit_logs_admin(self, client, auth_headers):
        """Test cleaning audit logs as admin."""
        response = client.post(
            "/api/v1/config/logs/cleanup?days_retention=90",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "detail" in data
