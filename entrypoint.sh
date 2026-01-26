#!/bin/sh
set -e

# Initialize database tables
python -c 'from nginx_manager.core.database import create_all_tables; create_all_tables()' 2>/dev/null || true

# Initialize security configuration (if not already done)
python -m nginx_manager.scripts.init_security_config 2>/dev/null || true

# Generate nginx config if backends and rules exist
python -c '
from nginx_manager.core import get_db
from nginx_manager.models.database import BackendServer, ProxyRule
from nginx_manager.core.nginx import NginxConfigGenerator
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
