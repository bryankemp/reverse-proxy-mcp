"""Nginx configuration generation and management."""

import json
import os
import shutil
import subprocess
from datetime import datetime

from jinja2 import Template
from sqlalchemy.orm import Session

from nginx_manager.core.logging import get_logger, log_nginx_operation
from nginx_manager.models.database import BackendServer, ProxyConfig, ProxyRule

logger = get_logger(__name__)

# Nginx configuration template with security features
NGINX_TEMPLATE = """# Auto-generated Nginx proxy configuration
# Generated at {{ timestamp }}
# DO NOT EDIT MANUALLY

# Backend upstream definitions
{% for backend in backends %}
upstream backend_{{ backend.id }} {
    server {{ backend.protocol }}://{{ backend.ip }}:{{ backend.port }};
}
{% endfor %}

{% if enable_default_ssl_server and default_ssl_cert_path and default_ssl_key_path %}
# Default SSL server (catches unknown/unmapped domains)
server {
    listen 443 ssl default_server;
    server_name _;
    ssl_certificate {{ default_ssl_cert_path }};
    ssl_certificate_key {{ default_ssl_key_path }};
    return 444;  # Close connection without response
}
{% endif %}

{% for rule in proxy_rules %}
{% if rule.force_https and rule.ssl_enabled %}
# HTTP to HTTPS redirect for {{ rule.frontend_domain }}
server {
    listen 80;
    server_name {{ rule.frontend_domain }};
    return 301 https://$host$request_uri;
}
{% endif %}

# Proxy rule: {{ rule.frontend_domain }} -> backend_{{ rule.backend_id }}
server {
    {% if rule.ssl_enabled %}
    listen 443 ssl;
    server_name {{ rule.frontend_domain }};
    
    # SSL certificate (TODO: integrate with SSLCertificate table)
    ssl_certificate {{ default_ssl_cert_path }};
    ssl_certificate_key {{ default_ssl_key_path }};
    {% else %}
    listen 80;
    server_name {{ rule.frontend_domain }};
    {% endif %}
    
    {% if rule.ip_list %}
    # IP Whitelist
    {% for ip in rule.ip_list %}
    allow {{ ip }};
    {% endfor %}
    deny all;
    {% endif %}
    
    {% if rule.enable_hsts and rule.ssl_enabled %}
    # HSTS Header
    add_header Strict-Transport-Security "max-age={{ rule.hsts_max_age }}; includeSubDomains" always;
    {% endif %}
    
    {% if rule.custom_headers %}
    # Custom Headers
    {% for key, value in rule.custom_headers_dict.items() %}
    add_header {{ key }} "{{ value }}" always;
    {% endfor %}
    {% endif %}
    
    location / {
        {% if rule.rate_limit %}
        # Rate Limiting
        limit_req zone=general burst=20 nodelay;
        {% endif %}
        
        # Proxy Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Proxy to backend
        proxy_pass {{ rule.backend_protocol }}://backend_{{ rule.backend_id }};
    }
}
{% endfor %}
"""


class NginxConfigGenerator:
    """Generate and manage Nginx configuration."""

    def __init__(self, config_path: str | None = None, backup_dir: str | None = None):
        """Initialize Nginx config generator.

        Args:
            config_path: Path to nginx.conf file (defaults to settings value)
            backup_dir: Directory for config backups (defaults to settings value)
        """
        from nginx_manager.core.config import settings

        self.config_path = config_path or settings.nginx_config_path
        self.backup_dir = backup_dir or settings.nginx_backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def generate_config(self, db: Session) -> str:
        """Generate Nginx configuration from database.

        Args:
            db: Database session

        Returns:
            Generated Nginx configuration as string
        """

        # Get global security config
        def get_config(key: str, default: str = "") -> str:
            config = db.query(ProxyConfig).filter(ProxyConfig.key == key).first()
            return config.value if config else default

        enable_default_ssl = get_config("enable_default_ssl_server", "false").lower() == "true"
        default_ssl_cert = get_config("default_ssl_cert_path", "/etc/ssl/certs/default.crt")
        default_ssl_key = get_config("default_ssl_key_path", "/etc/ssl/private/default.key")

        # Get all active backends and rules
        backends = db.query(BackendServer).filter(BackendServer.is_active).all()
        proxy_rules_db = db.query(ProxyRule).filter(ProxyRule.is_active).all()

        # Transform proxy rules for template
        proxy_rules = []
        for rule in proxy_rules_db:
            # Get backend
            backend = db.query(BackendServer).filter(BackendServer.id == rule.backend_id).first()

            ip_list = []
            if rule.ip_whitelist:
                try:
                    ip_list = json.loads(str(rule.ip_whitelist))
                except (json.JSONDecodeError, TypeError):
                    ip_list = []

            # Parse custom headers
            custom_headers_dict = {}
            if rule.custom_headers:
                try:
                    custom_headers_dict = json.loads(str(rule.custom_headers))
                except (json.JSONDecodeError, TypeError):
                    custom_headers_dict = {}

            proxy_rules.append(
                {
                    "frontend_domain": rule.frontend_domain,
                    "backend_id": rule.backend_id,
                    "backend_protocol": backend.protocol if backend else "http",
                    "access_control": rule.access_control,
                    "ip_whitelist": rule.ip_whitelist,
                    "ip_list": ip_list,
                    "enable_hsts": rule.enable_hsts,
                    "hsts_max_age": rule.hsts_max_age,
                    "enable_security_headers": rule.enable_security_headers,
                    "custom_headers": rule.custom_headers,
                    "custom_headers_dict": custom_headers_dict,
                    "rate_limit": rule.rate_limit,
                    "ssl_enabled": rule.ssl_enabled,
                    "force_https": rule.force_https,
                }
            )

        # Render template
        template = Template(NGINX_TEMPLATE)
        config = template.render(
            timestamp=datetime.utcnow().isoformat(),
            backends=backends,
            proxy_rules=proxy_rules,
            enable_default_ssl_server=enable_default_ssl,
            default_ssl_cert_path=default_ssl_cert,
            default_ssl_key_path=default_ssl_key,
        )

        return config

    def validate_config(self, config_content: str) -> tuple[bool, str]:
        """Validate Nginx configuration syntax.

        Args:
            config_content: Configuration content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Write temp config file for validation
        temp_path = f"{self.config_path}.test"
        try:
            with open(temp_path, "w") as f:
                f.write(config_content)

            # Test syntax
            result = subprocess.run(
                ["nginx", "-t", "-c", temp_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                log_nginx_operation("validate", True, "Configuration syntax OK")
                return True, "Configuration valid"
            else:
                log_nginx_operation("validate", False, result.stderr or "Unknown error")
                return False, result.stderr or "Unknown validation error"
        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False, str(e)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def reload_nginx(self) -> tuple[bool, str]:
        """Reload Nginx with HUP signal.

        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ["nginx", "-s", "reload"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                log_nginx_operation("reload", True, "Configuration reloaded")
                return True, "Nginx reloaded"
            else:
                log_nginx_operation("reload", False, result.stderr or "Unknown error")
                return False, result.stderr or "Reload failed"
        except subprocess.TimeoutExpired:
            return False, "Reload timeout"
        except Exception as e:
            logger.error(f"Nginx reload error: {e}")
            return False, str(e)

    def apply_config(self, db: Session) -> tuple[bool, str]:
        """Generate, validate, and apply new Nginx configuration.

        Args:
            db: Database session

        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate new config
            logger.info("Generating new Nginx configuration...")
            new_config = self.generate_config(db)

            # Validate new config
            logger.info("Validating configuration syntax...")
            is_valid, validation_msg = self.validate_config(new_config)
            if not is_valid:
                return False, f"Validation failed: {validation_msg}"

            # Backup current config
            if os.path.exists(self.config_path):
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.backup_dir}/nginx.conf.{timestamp}"
                shutil.copy2(self.config_path, backup_path)
                logger.info(f"Backed up current config to {backup_path}")

            # Write new config
            logger.info(f"Writing new config to {self.config_path}")
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                f.write(new_config)

            # Reload Nginx
            logger.info("Reloading Nginx...")
            success, reload_msg = self.reload_nginx()
            if success:
                logger.info("Configuration applied successfully")
                return True, "Configuration applied and Nginx reloaded"
            else:
                logger.error(f"Reload failed: {reload_msg}")
                return False, f"Reload failed: {reload_msg}"

        except Exception as e:
            logger.error(f"Error applying config: {e}")
            return False, f"Error applying config: {str(e)}"
