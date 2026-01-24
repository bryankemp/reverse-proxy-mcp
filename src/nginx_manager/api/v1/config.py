"""Configuration and audit log endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nginx_manager.api.dependencies import require_admin
from nginx_manager.core import get_db
from nginx_manager.models.database import ProxyConfig, User
from nginx_manager.models.schemas import AuditLogResponse
from nginx_manager.services.audit import AuditService

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=dict)
def get_config(db: Session = Depends(get_db), current_user: User = Depends(require_admin)) -> dict:
    """Get all proxy configuration (admin only)."""
    configs = db.query(ProxyConfig).all()
    return {config.key: config.value for config in configs}


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
