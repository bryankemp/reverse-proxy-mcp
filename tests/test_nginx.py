"""Tests for Nginx configuration generation and management."""

import pytest

from reverse_proxy_mcp.core.nginx import NginxConfigGenerator
from reverse_proxy_mcp.models.database import ProxyRule, SSLCertificate


@pytest.mark.unit
class TestNginxConfigGeneration:
    """Test Nginx configuration generation."""

    def test_generator_initialization(self, test_nginx_dir):
        """Test NginxConfigGenerator initializes correctly."""
        generator = NginxConfigGenerator(
            config_path=test_nginx_dir["config_path"],
            backup_dir=test_nginx_dir["backup_dir"],
        )
        assert generator.config_path == test_nginx_dir["config_path"]
        assert generator.backup_dir == test_nginx_dir["backup_dir"]

    def test_generate_empty_config(self, mock_nginx_generator, db):
        """Test generating config with no backends or rules."""
        generator = NginxConfigGenerator()
        config = generator.generate_config(db)
        assert isinstance(config, str)
        assert len(config) > 0
        # Should have basic header structure
        assert "Auto-generated" in config
        assert "# Backend upstream definitions" in config

    def test_generate_config_with_backend(self, mock_nginx_generator, db, backend_server):
        """Test generating config with a backend server."""
        generator = NginxConfigGenerator()
        config = generator.generate_config(db)
        assert isinstance(config, str)
        # Backend should be referenced in upstream block
        assert backend_server.name in config or backend_server.ip in config

    def test_generate_config_with_rule(self, mock_nginx_generator, db, backend_server, proxy_rule):
        """Test generating config with proxy rule."""
        generator = NginxConfigGenerator()
        config = generator.generate_config(db)
        assert isinstance(config, str)
        # Rule domain should appear in server_name directive
        assert proxy_rule.frontend_domain in config

    def test_validate_valid_config(self, mock_nginx_generator):
        """Test validating a valid nginx config."""
        generator = NginxConfigGenerator()
        valid, message = generator.validate_config("http { server { listen 80; } }")
        assert valid is True
        assert "valid" in message.lower()

    def test_apply_config_workflow(self, mock_nginx_generator, db, backend_server):
        """Test apply_config does backup, write, validate, and reload."""
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)

        # Mocked version always succeeds
        assert success is True
        assert "reload" in message.lower() or "applied" in message.lower()

    def test_reload_nginx(self, mock_nginx_generator):
        """Test nginx reload (mocked)."""
        generator = NginxConfigGenerator()
        success, message = generator.reload_nginx()
        assert success is True
        assert "reload" in message.lower()


@pytest.mark.integration
class TestNginxEndToEnd:
    """End-to-end tests for Nginx config workflow."""

    def test_config_reload_endpoint(self, client, auth_headers):
        """Test nginx reload endpoint."""
        response = client.post("/api/v1/config/reload", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "detail" in data

    def test_config_reload_unauthorized(self, client, user_auth_headers):
        """Test nginx reload requires admin."""
        response = client.post("/api/v1/config/reload", headers=user_auth_headers)
        assert response.status_code == 403

    def test_get_nginx_config(self, client, auth_headers):
        """Test getting current nginx config."""
        response = client.get("/api/v1/config/nginx", headers=auth_headers)
        assert response.status_code == 200
        config = response.json()
        # Should return config content
        assert isinstance(config, (str, dict))

    def test_full_workflow_config_generation(
        self, client, auth_headers, db, backend_server, proxy_rule, mock_nginx_generator
    ):
        """Test complete workflow: create resources -> generate config -> reload."""
        # Generate config
        from reverse_proxy_mcp.core.nginx import NginxConfigGenerator

        generator = NginxConfigGenerator()
        config = generator.generate_config(db)

        # Verify config contains our resources
        assert backend_server.name in config or backend_server.ip in config
        assert proxy_rule.frontend_domain in config

        # Validate config
        valid, message = generator.validate_config(config)
        assert valid is True

        # Apply config (does backup, write, validate, reload)
        success, message = generator.apply_config(db)
        assert success is True


@pytest.mark.integration
def test_config_with_ssl_certificate(client, auth_headers, db, backend_server):
    """Test config generation with SSL certificate."""
    from reverse_proxy_mcp.core.nginx import NginxConfigGenerator

    # Create SSL certificate
    cert = SSLCertificate(
        name="Test SSL",
        domain="*.test.com",
        cert_path="/etc/nginx/certs/test.crt",
        key_path="/etc/nginx/certs/test.key",
        certificate_type="wildcard",
        is_default=True,
        uploaded_by=1,
    )
    db.add(cert)
    db.commit()

    # Create proxy rule with certificate
    rule = ProxyRule(
        frontend_domain="api.test.com",
        backend_id=backend_server.id,
        certificate_id=cert.id,
        ssl_enabled=True,
        force_https=True,
        is_active=True,
        created_by=1,
    )
    db.add(rule)
    db.commit()

    # Generate config
    generator = NginxConfigGenerator()
    config = generator.generate_config(db)

    # Should contain SSL directives
    assert "ssl_certificate" in config
    assert cert.cert_path in config or "test.crt" in config
    assert "443" in config  # HTTPS port
