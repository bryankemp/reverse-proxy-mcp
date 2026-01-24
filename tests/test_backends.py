"""Unit tests for backend server endpoints."""

import pytest
from fastapi import status


@pytest.mark.unit
class TestBackendServers:
    """Test backend server endpoints."""

    def test_list_backends(self, client, user_auth_headers, backend_server):
        """Test listing backends."""
        response = client.get("/api/v1/backends", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        backends = response.json()
        assert len(backends) > 0
        assert any(b["name"] == "test-backend" for b in backends)

    def test_get_backend(self, client, user_auth_headers, backend_server):
        """Test getting specific backend."""
        response = client.get(f"/api/v1/backends/{backend_server.id}", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "test-backend"
        assert data["ip"] == "192.168.1.100"
        assert data["port"] == 8080

    def test_get_backend_not_found(self, client, user_auth_headers):
        """Test getting nonexistent backend."""
        response = client.get("/api/v1/backends/99999", headers=user_auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_backend_admin(self, client, auth_headers):
        """Test creating backend as admin."""
        response = client.post(
            "/api/v1/backends",
            json={
                "name": "new-backend",
                "ip": "192.168.1.101",
                "port": 8081,
                "service_description": "New backend",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "new-backend"
        assert data["ip"] == "192.168.1.101"

    def test_create_backend_duplicate_name(self, client, auth_headers, backend_server):
        """Test creating backend with duplicate name."""
        response = client.post(
            "/api/v1/backends",
            json={
                "name": "test-backend",
                "ip": "192.168.1.102",
                "port": 8082,
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_backend_unauthorized(self, client, user_auth_headers):
        """Test creating backend as regular user."""
        response = client.post(
            "/api/v1/backends",
            json={
                "name": "unauthorized-backend",
                "ip": "192.168.1.103",
                "port": 8083,
            },
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_backend_admin(self, client, auth_headers, backend_server):
        """Test updating backend as admin."""
        response = client.put(
            f"/api/v1/backends/{backend_server.id}",
            json={"ip": "192.168.1.200", "port": 9090},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ip"] == "192.168.1.200"
        assert data["port"] == 9090

    def test_delete_backend_admin(self, client, auth_headers, backend_server):
        """Test deleting backend as admin."""
        backend_id = backend_server.id
        response = client.delete(
            f"/api/v1/backends/{backend_id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_test_backend_connectivity(self, client, user_auth_headers, backend_server):
        """Test backend connectivity test endpoint."""
        response = client.post(
            f"/api/v1/backends/{backend_server.id}/test",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "response_time_ms" in data


@pytest.mark.unit
class TestProxyRules:
    """Test proxy rule endpoints."""

    def test_list_proxy_rules(self, client, user_auth_headers, proxy_rule):
        """Test listing proxy rules."""
        response = client.get("/api/v1/proxy-rules", headers=user_auth_headers)
        assert response.status_code == status.HTTP_200_OK
        rules = response.json()
        assert len(rules) > 0
        assert any(r["frontend_domain"] == "test.example.com" for r in rules)

    def test_get_proxy_rule(self, client, user_auth_headers, proxy_rule):
        """Test getting specific proxy rule."""
        response = client.get(
            f"/api/v1/proxy-rules/{proxy_rule.id}",
            headers=user_auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["frontend_domain"] == "test.example.com"
        assert data["access_control"] == "public"

    def test_create_proxy_rule_admin(self, client, auth_headers, backend_server):
        """Test creating proxy rule as admin."""
        response = client.post(
            "/api/v1/proxy-rules",
            json={
                "frontend_domain": "new-rule.example.com",
                "backend_id": backend_server.id,
                "access_control": "public",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["frontend_domain"] == "new-rule.example.com"

    def test_create_proxy_rule_duplicate_domain(self, client, auth_headers, proxy_rule):
        """Test creating proxy rule with duplicate domain."""
        response = client.post(
            "/api/v1/proxy-rules",
            json={
                "frontend_domain": "test.example.com",
                "backend_id": proxy_rule.backend_id,
                "access_control": "public",
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_update_proxy_rule_admin(self, client, auth_headers, proxy_rule, backend_server):
        """Test updating proxy rule as admin."""
        response = client.put(
            f"/api/v1/proxy-rules/{proxy_rule.id}",
            json={"access_control": "internal"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_control"] == "internal"

    def test_delete_proxy_rule_admin(self, client, auth_headers, proxy_rule):
        """Test deleting proxy rule as admin."""
        rule_id = proxy_rule.id
        response = client.delete(
            f"/api/v1/proxy-rules/{rule_id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
