#!/bin/bash

# Nginx Manager Deployment Script
# Deploys to slug.kempville.com via SSH

set -e

REMOTE_HOST="grimlock.kempville.com"
REMOTE_USER="bryan"
REMOTE_DIR="~/nginx-manager"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"

echo "🚀 Deploying Nginx Manager to $REMOTE_HOST..."

# 0. Build Flutter web (release)
if command -v flutter >/dev/null 2>&1; then
  echo "🛠️  Building Flutter web (release)..."
  (cd "$LOCAL_DIR/webui" && flutter build web --release --no-tree-shake-icons)
else
  echo "⚠️  Flutter not found locally; assuming webui/build/web is already a release build"
fi

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
  --exclude='webui/.dart_tool' \
  --exclude='.env' \
  "$LOCAL_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# 3. Create .env file on remote if it doesn't exist
echo "⚙️  Configuring environment..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cat > $REMOTE_DIR/.env << 'ENVEOF'
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/nginx_manager.db
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_EMAIL=admin@grimlock.kempville.com
ADMIN_PASSWORD=$(openssl rand -base64 12)
CORS_ORIGINS='http://grimlock.kempville.com:5100,https://grimlock.kempville.com,http://grimlock.kempville.com'
API_PORT=8000
MCP_PORT=5000
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
METRICS_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=90
ENVEOF
"

# 4. Build image on remote (using podman if docker not available)
echo "🏗️  Building container image..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && docker build -t nginx-manager:latest ."

# 5. Stop existing container if running
echo "⏹️  Stopping existing container..."
ssh "$REMOTE_USER@$REMOTE_HOST" "docker stop nginx-manager 2>/dev/null || true && docker rm nginx-manager 2>/dev/null || true"

# 6. Ensure certs exist
echo "🔐 Ensuring SSL certs..."
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/certs && cd $REMOTE_DIR/certs && [ -f server.crt ] || openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes -subj '/CN=grimlock.kempville.com' && chmod 644 server.crt && chmod 600 server.key"

# 7. Start new container
echo "🎬 Starting new container..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && docker run -d \
  --name nginx-manager \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  -p 5100:3000 \
  -v \$(pwd)/data:/app/data \
  -v \$(pwd)/certs:/etc/nginx/certs \
  -v \$(pwd)/logs:/var/log \
  --env-file .env \
  nginx-manager:latest"

# 7. Verify deployment
echo "✅ Verifying deployment..."
sleep 5
if ssh "$REMOTE_USER@$REMOTE_HOST" "curl -f http://localhost/health && curl -kfs https://localhost/health >/dev/null"; then
  echo "✨ Deployment successful!"
else
  echo "❌ Health check failed. Check logs with: docker-compose logs"
  exit 1
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
echo "To view logs: ssh $REMOTE_USER@$REMOTE_HOST 'docker logs -f nginx-manager'"
echo "To stop: ssh $REMOTE_USER@$REMOTE_HOST 'docker stop nginx-manager'"
echo "To restart: ssh $REMOTE_USER@$REMOTE_HOST 'docker restart nginx-manager'"
