"""Configuration and audit log endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import require_admin
from reverse_proxy_mcp.core import get_db
from reverse_proxy_mcp.models.database import ProxyConfig, User
from reverse_proxy_mcp.models.schemas import AuditLogResponse
from reverse_proxy_mcp.services.audit import AuditService

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=dict)
def get_config(db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> dict:
    """Get all proxy configuration (admin only)."""
    configs = db.query(ProxyConfig).all()
    return {config.key: config.value for config in configs}


# Nginx config endpoints (must come before /{key} to avoid path conflicts)
@router.get("/nginx")
def get_nginx_config(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Get current Nginx configuration file content (admin only)."""
    import os

    from reverse_proxy_mcp.core import settings
    from reverse_proxy_mcp.core.nginx import NginxConfigGenerator

    generator = NginxConfigGenerator()
    config_path = settings.nginx_config_path

    # If config file doesn't exist, generate it
    if not os.path.exists(config_path):
        config = generator.generate_config(db)
    else:
        with open(config_path) as f:
            config = f.read()

    return {"config": config, "path": config_path}


@router.post("/reload")
def reload_nginx(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Reload Nginx with current configuration (admin only)."""
    from reverse_proxy_mcp.core.nginx import NginxConfigGenerator

    generator = NginxConfigGenerator()
    success, message = generator.reload_nginx()

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    # Audit log
    AuditService.log_config_changed(
        db, current_user, {"action": "nginx_reload", "message": message}
    )

    return {"success": True, "message": message}


# Config key/value endpoints
@router.get("/{key}")
def get_config_value(
    key: str, db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Get specific configuration value (admin only)."""
    config = db.query(ProxyConfig).filter(ProxyConfig.key == key).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Configuration key not found"
        )
    return {"key": key, "value": config.value}


@router.put("/{key}")
def set_config_value(
    key: str,
    value: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Set configuration value (admin only)."""
    config = db.query(ProxyConfig).filter(ProxyConfig.key == key).first()

    if config:
        old_value = config.value
        config.value = value
    else:
        old_value = None
        config = ProxyConfig(key=key, value=value)
        db.add(config)

    db.commit()

    # Audit log
    AuditService.log_config_changed(
        db, current_user, {"key": key, "old_value": old_value, "new_value": value}
    )

    return {"key": key, "value": value}


# Audit Log Endpoints
@router.get("/logs/all", response_model=list[AuditLogResponse])
def list_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[AuditLogResponse]:
    """Get audit logs (admin only)."""
    return AuditService.get_audit_logs(db, limit=limit)


@router.get("/logs/user/{user_id}", response_model=list[AuditLogResponse])
def get_user_audit_logs(
    user_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[AuditLogResponse]:
    """Get audit logs for specific user (admin only)."""
    return AuditService.get_user_audit_logs(db, user_id, limit=limit)


@router.get("/logs/resource/{resource_type}/{resource_id}", response_model=list[AuditLogResponse])
def get_resource_audit_logs(
    resource_type: str,
    resource_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[AuditLogResponse]:
    """Get audit logs for specific resource (admin only)."""
    return AuditService.get_resource_audit_logs(db, resource_type, resource_id, limit=limit)


@router.post("/logs/cleanup")
def cleanup_audit_logs(
    days_retention: int = 90,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Delete old audit logs (admin only)."""
    deleted_count = AuditService.cleanup_old_logs(db, days_retention)
    return {"detail": f"Deleted {deleted_count} audit logs older than {days_retention} days"}


@router.get("/debug")
def get_debug_info(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Get debug information (admin only)."""
    from reverse_proxy_mcp.core import settings
    from reverse_proxy_mcp.models.database import BackendServer, ProxyRule

    return {
        "debug_mode": settings.debug,
        "app_version": settings.app_version,
        "backend_count": db.query(BackendServer).count(),
        "active_backend_count": db.query(BackendServer).filter(BackendServer.is_active).count(),
        "proxy_rule_count": db.query(ProxyRule).count(),
        "active_proxy_rule_count": db.query(ProxyRule).filter(ProxyRule.is_active).count(),
        "nginx_config_path": settings.nginx_config_path,
        "database_url": settings.database_url,
        "log_level": "DEBUG" if settings.debug else "INFO",
    }


# Security Config Endpoints
@router.get("/security")
def get_security_config(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> dict:
    """Get security configuration (admin only)."""
    import json

    def get_config_value(key: str, default: str = "") -> str:
        config = db.query(ProxyConfig).filter(ProxyConfig.key == key).first()
        return config.value if config else default

    headers_json = get_config_value("default_security_headers", "{}")
    try:
        headers = json.loads(headers_json)
    except json.JSONDecodeError:
        headers = {}

    return {
        "security_headers": headers,
        "ssl_protocols": get_config_value("ssl_protocols", "TLSv1.2 TLSv1.3"),
        "ssl_ciphers": get_config_value("ssl_ciphers", ""),
        "rate_limit_zone": get_config_value("rate_limit_zone", "general:10m rate=100r/s"),
        "server_tokens": get_config_value("server_tokens", "off"),
        "enable_default_ssl_server": get_config_value("enable_default_ssl_server", "false")
        == "true",
    }


@router.put("/security/headers")
def update_security_headers(
    headers: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Update security headers configuration (admin only)."""
    import json

    headers_json = json.dumps(headers)
    config = db.query(ProxyConfig).filter(ProxyConfig.key == "default_security_headers").first()

    if config:
        old_value = config.value
        config.value = headers_json
    else:
        old_value = None
        config = ProxyConfig(key="default_security_headers", value=headers_json)
        db.add(config)

    db.commit()

    # Audit log
    AuditService.log_config_changed(
        db,
        current_user,
        {"key": "default_security_headers", "old_value": old_value, "new_value": headers_json},
    )

    return {"success": True, "headers": headers}
