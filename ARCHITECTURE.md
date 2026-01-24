# Nginx Manager - Architecture

## Single Container Deployment

**Decision:** Nginx Manager uses a **single unified container** instead of microservices.

### Rationale

1. **Simplicity**: Single container to deploy, manage, and debug
2. **Performance**: No inter-container networking overhead
3. **Resource Efficiency**: Lower memory footprint, faster startup
4. **Operational Simplicity**: One process to monitor, one image to maintain
5. **Suitable Scale**: Proxy management doesn't require microservices complexity

### Container Architecture

```
┌─────────────────────────────────────────────────────┐
│  Nginx Manager Container (Alpine Linux + Python)    │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Supervisord (Process Manager)                  │ │
│  └───────┬──────────────┬──────────────┬──────────┘ │
│          │              │              │             │
│  ┌───────▼──────┐ ┌────▼──────┐ ┌────▼────────┐   │
│  │ Nginx        │ │ FastAPI   │ │ MCP Server  │   │
│  │ Ports 80,443 │ │ Port 8000 │ │ Port 5000   │   │
│  │ Serves WebUI │ │ REST API  │ │ AI Tools    │   │
│  └──────────────┘ └───────────┘ └─────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ SQLite Database (/data/nginx_manager.db)    │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ File System                                  │   │
│  │ - /data/certs    (SSL certificates)          │   │
│  │ - /data/logs     (Application & Nginx logs)  │   │
│  │ - /data/config   (Generated Nginx configs)   │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Deployment

**Single Command:**
```bash
docker run -d \
  -p 80:80 \
  -p 443:443 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key \
  nginx-manager:latest
```

**With Docker Compose** (optional for easier management):
```yaml
version: '3.8'
services:
  nginx-manager:
    image: nginx-manager:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

### Process Management (Supervisord)

**supervisord.conf** manages all services:
```ini
[supervisord]
nodaemon=true

[program:nginx]
command=/usr/sbin/nginx -g 'daemon off;'
autostart=true
autorestart=true
priority=100

[program:api]
command=uvicorn nginx_manager.api.main:app --host 0.0.0.0 --port 8000
directory=/app
autostart=true
autorestart=true
priority=200

[program:mcp-server]
command=python -m nginx_manager.mcp
directory=/app
autostart=true
autorestart=true
priority=300
```

### Benefits

- ✅ **Single image to build and deploy**
- ✅ **Shared file system** - no volume synchronization issues
- ✅ **Direct function calls** - no HTTP overhead between components
- ✅ **Easier debugging** - all logs in one place
- ✅ **Lower resource usage** - ~200MB total vs 500MB+ for microservices
- ✅ **Faster startup** - 5-10 seconds vs 30+ seconds
- ✅ **Simpler networking** - no container networking complexity

### Trade-offs

- Cannot scale components independently (not needed for this use case)
- Single point of failure (mitigated by proper health checks and restart policies)
- All components share same resource limits (acceptable for proxy management)

### Health Checks

All services expose health endpoints:
- `http://localhost:8000/health` - API server
- `http://localhost:5000/health` - MCP server  
- `http://localhost/nginx_health` - Nginx status

Docker health check monitors API endpoint as primary indicator.

### WebUI Deployment

Static files built from Flutter project and served directly by Nginx:
- Build: `flutter build web`
- Output: `build/web/` → `/usr/share/nginx/html/`
- Nginx serves at root path `/`
- API proxied at `/api/`
- MCP proxied at `/mcp/`

### Production Considerations

1. **Resource Limits**: Set via Docker (`--memory=512m --cpus=0.5`)
2. **Log Rotation**: Configured in supervisord
3. **Health Monitoring**: Docker health check + external monitoring
4. **Backup**: Volume mount `/data` and backup regularly
5. **Updates**: Build new image, stop old container, start new
6. **Rollback**: Keep previous image tagged for quick rollback

## Implementation Status

- ✅ Phase 1-3: Core API and testing complete (75% coverage)
- 🔄 Phase 4: MCP Server - In Progress
- ⬜ Phase 5: Flutter WebUI
- ⬜ Phase 6: Documentation
- ⬜ Phase 7: Single Container Dockerfile + Supervisord
