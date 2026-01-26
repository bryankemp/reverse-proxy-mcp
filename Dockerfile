# Stage 1: Build Flutter web app
FROM ghcr.io/cirruslabs/flutter:stable AS flutter-builder

WORKDIR /app/webui
COPY webui/pubspec.yaml webui/pubspec.lock ./
RUN flutter pub get

COPY webui/ ./
RUN flutter build web --release

# Stage 2: Python app with Nginx
FROM python:3.11-alpine
RUN apk add --no-cache nginx supervisor curl

WORKDIR /app

# Copy Python app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Copy Flutter web build from builder stage
COPY --from=flutter-builder /app/webui/build/web /app/webui/build/web

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/log/supervisor /var/log /app/data /etc/nginx/conf.d && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log && \
    chmod -R 777 /var/log/nginx /var/log/supervisor /var/log

# Copy Nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy Supervisord config
COPY supervisord.conf /etc/supervisord.conf

# Initialize database and create admin user on startup
RUN mkdir -p /app/data && python -c 'from nginx_manager.core.database import create_all_tables; create_all_tables()' 2>/dev/null || true

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost/health || exit 1

# Run supervisord directly
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
