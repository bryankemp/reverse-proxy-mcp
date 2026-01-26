"""Unit tests for certificate and configuration endpoints."""

import io

import pytest
from fastapi import status

# Sample self-signed certificate for testing
TEST_CERT = """-----BEGIN CERTIFICATE-----
MIICpDCCAYwCCQDU7T0Q3Qj5qTANBgkqhkiG9w0BAQsFADAUMRIwEAYDVQQDDAkq
LnRlc3QuY29tMB4XDTIzMTIwMTAwMDAwMFoXDTI0MTIwMTAwMDAwMFowFDESMBAG
A1UEAwwJKi50ZXN0LmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEB
AKqK1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN
OPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZab
IwIDAQABMA0GCSqGSIb3DQEBCwUAA4IBAQBxyz123456789ABCDEFGHIJK
-----END CERTIFICATE-----"""

TEST_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCqitXYZabcdefgh
ijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv
wxyzABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzABCDEFGHIJ
KLMNOPQRSTUVWXYZabIDAQABAoIBAExample1234567890
-----END PRIVATE KEY-----"""


@pytest.mark.unit
class TestCertificates:
    """Test certificate management endpoints."""

    def test_list_certificates(self, client, user_auth_headers):
        """Test listing certificates."""
        response = client.get("/api/v1/certificates", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        certs = response.json()
        assert isinstance(certs, list)

    def test_list_certificates_dropdown(self, client, user_auth_headers):
        """Test listing certificates for dropdown."""
        response = client.get("/api/v1/certificates/dropdown", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        certs = response.json()
        assert isinstance(certs, list)

    def test_upload_certificate_unauthorized(self, client, user_auth_headers):
        """Test uploading certificate as non-admin."""
        files = {
            "cert_file": ("cert.pem", io.BytesIO(TEST_CERT.encode()), "text/plain"),
            "key_file": ("key.pem", io.BytesIO(TEST_KEY.encode()), "text/plain"),
        }
        data = {"name": "Test Certificate", "domain": "*.test.com", "is_default": "false"}
        response = client.post(
            "/api/v1/certificates", headers=user_auth_headers, files=files, data=data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_certificate_not_found(self, client, user_auth_headers):
        """Test getting nonexistent certificate."""
        response = client.get("/api/v1/certificates/9999", headers=user_auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_set_default_unauthorized(self, client, user_auth_headers):
        """Test setting default certificate as non-admin."""
        response = client.put("/api/v1/certificates/1/set-default", headers=user_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_certificate_unauthorized(self, client, user_auth_headers):
        """Test deleting certificate as non-admin."""
        response = client.delete("/api/v1/certificates/1", headers=user_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

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

    def test_set_default_certificate_not_found(self, client, auth_headers):
        """Test setting nonexistent certificate as default."""
        response = client.put("/api/v1/certificates/9999/set-default", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_certificate_not_found(self, client, auth_headers):
        """Test deleting nonexistent certificate."""
        response = client.delete("/api/v1/certificates/9999", headers=auth_headers)
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
