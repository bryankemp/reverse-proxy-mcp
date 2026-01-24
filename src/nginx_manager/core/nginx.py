"""Nginx configuration generation and management."""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime

from jinja2 import Template
from sqlalchemy.orm import Session

from nginx_manager.models.database import BackendServer, ProxyRule

logger = logging.getLogger(__name__)

# Nginx configuration template
NGINX_TEMPLATE = """# Auto-generated Nginx configuration
# Generated at {{ timestamp }}
# DO NOT EDIT MANUALLY

# Load dynamic modules
include /etc/nginx/modules-enabled/*.conf;

user nginx;
worker_processes auto;
pid /var/run/nginx.pid;

events {
    worker_connections 768;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/atom+xml image/svg+xml;

    # HTTP to HTTPS redirect
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # Backend upstream definitions
    {% for backend in backends %}
    upstream backend_{{ backend.id }} {
        server {{ backend.ip }}:{{ backend.port }};
    }
    {% endfor %}

    # HTTPS server block
    server {
        listen 443 ssl http2 default_server;
        listen [::]:443 ssl http2 default_server;
        server_name _;

        # SSL certificates (default wildcard)
        ssl_certificate /etc/nginx/certs/default.crt;
        ssl_certificate_key /etc/nginx/certs/default.key;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # Proxy rules
        {% for rule in proxy_rules %}
        location ~* ^{{ rule.location_regex }}(/|$) {
            {% if rule.access_control == 'internal' %}
            {% if rule.ip_whitelist %}
            # IP whitelist
            {% for ip in rule.ip_list %}
            allow {{ ip }};
            {% endfor %}
            deny all;
            {% else %}
            # Internal only - default deny all
            deny all;
            {% endif %}
            {% endif %}

            proxy_pass http://backend_{{ rule.backend_id }};
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        {% endfor %}

        # Health check endpoint
        location /nginx_health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
}
"""


class NginxConfigGenerator:
    """Generate and manage Nginx configuration."""

    def __init__(self, config_path: str, backup_dir: str = "/etc/nginx/backup"):
        """Initialize Nginx config generator.

        Args:
            config_path: Path to nginx.conf file
            backup_dir: Directory for config backups
        """
        self.config_path = config_path
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def generate_config(self, db: Session) -> str:
        """Generate Nginx configuration from database.

        Args:
            db: Database session

        Returns:
            Generated Nginx configuration as string
        """
        # Get all active backends and rules
        backends = db.query(BackendServer).filter(BackendServer.is_active).all()
        proxy_rules_db = db.query(ProxyRule).filter(ProxyRule.is_active).all()

        # Transform proxy rules for template
        proxy_rules = []
        for rule in proxy_rules_db:

            ip_list = []
            if rule.ip_whitelist:
                try:
                    ip_list = json.loads(rule.ip_whitelist)
                except (json.JSONDecodeError, TypeError):
                    ip_list = []

            proxy_rules.append(
                {
                    "frontend_domain": rule.frontend_domain,
                    "location_regex": rule.frontend_domain.replace(".", r"\.").replace("*", ".*"),
                    "backend_id": rule.backend_id,
                    "access_control": rule.access_control,
                    "ip_whitelist": rule.ip_whitelist,
                    "ip_list": ip_list,
                }
            )

        # Render template
        template = Template(NGINX_TEMPLATE)
        config = template.render(
            timestamp=datetime.utcnow().isoformat(),
            backends=backends,
            proxy_rules=proxy_rules,
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
                return True, "Configuration valid"
            else:
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
                logger.info("Nginx reloaded successfully")
                return True, "Nginx reloaded"
            else:
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
