#!/bin/sh
set -e

# Ensure Nginx log directory exists with proper permissions
mkdir -p /var/log/nginx
touch /var/log/nginx/access.log /var/log/nginx/error.log
chmod -R 777 /var/log/nginx

# Initialize database tables
python -c 'from reverse_proxy_mcp.core.database import create_all_tables; create_all_tables()' 2>/dev/null || true

# Initialize security configuration (if not already done)
python -m reverse_proxy_mcp.scripts.init_security_config 2>/dev/null || true

# Generate nginx config if backends and rules exist
python -c '
from reverse_proxy_mcp.core import get_db
from reverse_proxy_mcp.models.database import BackendServer, ProxyRule
from reverse_proxy_mcp.core.nginx import NginxConfigGenerator
import os
import sys

try:
    db = next(get_db())
    backends = db.query(BackendServer).filter(BackendServer.is_active == True).all()
    rules = db.query(ProxyRule).filter(ProxyRule.is_active == True).all()
    
    if backends and rules:
        print(f"Found {len(backends)} backend(s) and {len(rules)} rule(s) - generating nginx config...")
        generator = NginxConfigGenerator()
        
        # Just generate and write the config file (nginx will read it on startup)
        config = generator.generate_config(db)
        config_path = generator.config_path
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            f.write(config)
        print(f"Nginx configuration written to {config_path} - nginx will load on startup")
    else:
        print("No active backends/rules found - skipping config generation")
except Exception as e:
    print(f"Error during startup config generation: {e}", file=sys.stderr)
' 2>/dev/null || true

# Start supervisord
exec supervisord -c /etc/supervisord.conf
