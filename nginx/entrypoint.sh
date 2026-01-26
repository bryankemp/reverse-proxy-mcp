#!/bin/bash
set -e

echo "Starting Reverse Proxy MCP initialization..."

# Create required directories
mkdir -p /app/data /etc/nginx/certs /var/log/nginx /var/cache/nginx

# Initialize database if needed
if [ ! -f /app/data/reverse_proxy_mcp.db ]; then
    echo "Initializing database..."
    cd /app
    /app/.venv/bin/python -c "from reverse_proxy_mcp.core.database import create_all_tables; create_all_tables()"
    echo "Database initialized"
fi

# Create admin user if it doesn't exist
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "Checking admin user..."
    cd /app
/app/.venv/bin/python -c "
from reverse_proxy_mcp.core.database import SessionLocal
from reverse_proxy_mcp.models.database import User
from reverse_proxy_mcp.core.security import hash_password

db = SessionLocal()
admin = db.query(User).filter(User.email == '$ADMIN_EMAIL').first()
if not admin:
    print('Creating admin user...')
    user = User(
        email='$ADMIN_EMAIL',
        username='admin',
        password_hash=hash_password('$ADMIN_PASSWORD'),
        role='admin',
        is_active=True
    )
    db.add(user)
    db.commit()
    print('Admin user created')
else:
    print('Admin user exists')
db.close()
"
fi

# Generate default nginx.conf if needed
if [ ! -f /etc/nginx/nginx.conf ]; then
    echo "Generating default nginx.conf..."
    cat > /etc/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # API upstream
    upstream api {
        server localhost:8000;
    }

    # WebUI upstream
    upstream webui {
        server localhost:3000;
    }

    # Default server
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        location /api {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            root /app/webui/build/web;
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF
fi

echo "Initialization complete"
exec supervisord -c /app/supervisord.conf
