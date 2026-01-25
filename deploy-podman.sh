#!/bin/bash

# Nginx Manager Deployment Script (Podman)
# Deploys to turbo.kempville.com via SSH using Podman

set -e

REMOTE_HOST="turbo.kempville.com"
REMOTE_USER="bryan"
REMOTE_DIR="~/nginx-manager"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying Nginx Manager to $REMOTE_HOST..."

# 1. Create remote directory
echo "📁 Creating remote directory..."
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# 2. Copy project files
echo "📤 Uploading project files..."
rsync -avz --delete \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='venv' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='htmlcov' \
  --exclude='.mypy_cache' \
  --exclude='webui/build' \
  --exclude='webui/.dart_tool' \
  --exclude='.env' \
  "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# 3. Create .env file on remote
echo "⚙️  Configuring environment..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/.env << 'ENVEOF'
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/nginx_manager.db
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_EMAIL=admin@turbo.kempville.com
ADMIN_PASSWORD=$(openssl rand -base64 12)
CORS_ORIGINS='http://turbo.kempville.com:5100,https://turbo.kempville.com:443,http://turbo.kempville.com:80'
API_PORT=8000
MCP_PORT=5000
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
METRICS_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=90
ENVEOF
"

# 4. Build image on remote with podman
echo "🏗️  Building container image with podman..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && podman build --no-cache -t nginx-manager:latest ."

# 5. Create required directories
echo "📂 Creating required directories..."
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/data $REMOTE_DIR/certs $REMOTE_DIR/logs"

# 6. Stop existing container if running
echo "⏹️  Stopping existing container..."
ssh "$REMOTE_USER@$REMOTE_HOST" "podman stop nginx-manager 2>/dev/null || true && podman rm nginx-manager 2>/dev/null || true"

# 7. Start new container with podman (using higher ports due to privilege restrictions)
echo "🎬 Starting new container..."
echo "  Using ports: 8080->80, 8443->443, 5100->3000"
ssh "$REMOTE_USER@$REMOTE_HOST" 'cd $HOME/nginx-manager && podman run -d \
  --name nginx-manager \
  --restart=always \
  -p 8080:80 \
  -p 8443:443 \
  -p 5100:3000 \
-v '\''$(pwd)'/data:/app/data:Z \
  -v '\''$(pwd)'/certs:/etc/nginx/certs:Z \
  -v '\''$(pwd)'/logs:/var/log:Z \\
  --env-file .env \
  nginx-manager:latest"

# 8. Verify deployment
echo "✅ Verifying deployment..."
sleep 5
if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -f http://localhost:5100 >/dev/null 2>&1 || curl -f http://localhost:80 >/dev/null 2>&1"; then
  echo "✨ Deployment successful!"
else
  echo "⚠️  Service may still be starting. Checking logs..."
  ssh "$REMOTE_USER@$REMOTE_HOST" "podman logs nginx-manager | tail -20" || true
fi

echo ""
echo "📝 Deployment Summary:"
echo "  Host: $REMOTE_HOST"
echo "  Directory: $REMOTE_DIR"
echo "  WebUI/Admin: http://$REMOTE_HOST:5100 (Flutter admin interface)"
echo "  HTTP Proxy: http://$REMOTE_HOST:80 (reverse proxy)"
echo "  HTTPS Proxy: https://$REMOTE_HOST:443 (reverse proxy with HTTPS)"
echo "  API Docs: http://$REMOTE_HOST:5100/docs (available via admin UI)"
echo ""
echo "To view logs: ssh $REMOTE_USER@$REMOTE_HOST 'podman logs -f nginx-manager'"
echo "To stop: ssh $REMOTE_USER@$REMOTE_HOST 'podman stop nginx-manager'"
echo "To restart: ssh $REMOTE_USER@$REMOTE_HOST 'podman restart nginx-manager'"
