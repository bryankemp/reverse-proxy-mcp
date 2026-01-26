"""Initialize global security configuration in ProxyConfig table."""

import json
from nginx_manager.core.database import SessionLocal
from nginx_manager.models.database import ProxyConfig


def init_security_config():
    """Initialize default security configuration."""
    db = SessionLocal()

    configs = {
        # SSL/TLS Settings
        "ssl_protocols": "TLSv1.2 TLSv1.3",
        "ssl_ciphers": "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384",
        "ssl_prefer_server_ciphers": "on",
        # Security Headers
        "default_security_headers": json.dumps(
            {
                "X-Frame-Options": "SAMEORIGIN",
                "X-Content-Type-Options": "nosniff",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
            }
        ),
        # Rate Limiting
        "rate_limit_zone": "general:10m rate=100r/s",
        "rate_limit_status": "429",
        # Server Settings
        "server_tokens": "off",
        # Gzip Settings
        "gzip": json.dumps(
            {
                "enabled": True,
                "vary": True,
                "proxied": "any",
                "comp_level": 6,
                "types": "text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript",
            }
        ),
        # Default SSL Certificate (if available)
        "enable_default_ssl_server": "true",
        "default_ssl_cert_path": "/etc/ssl/certs/default.crt",
        "default_ssl_key_path": "/etc/ssl/private/default.key",
    }

    for key, value in configs.items():
        # Check if exists
        existing = db.query(ProxyConfig).filter(ProxyConfig.key == key).first()
        if not existing:
            config = ProxyConfig(key=key, value=value)
            db.add(config)
            print(f"Added config: {key}")
        else:
            print(f"Config already exists: {key}")

    db.commit()
    print("Security configuration initialized successfully!")


if __name__ == "__main__":
    init_security_config()
