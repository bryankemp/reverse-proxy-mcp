#!/bin/sh
set -e

# Initialize database tables
python -c 'from nginx_manager.core.database import create_all_tables; create_all_tables()' 2>/dev/null || true

# Initialize security configuration (if not already done)
python -m nginx_manager.scripts.init_security_config 2>/dev/null || true

# Start supervisord
exec supervisord -c /etc/supervisord.conf
