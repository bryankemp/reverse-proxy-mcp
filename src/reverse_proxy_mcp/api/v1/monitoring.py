"""Health and metrics monitoring endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import require_user
from reverse_proxy_mcp.core import get_db, settings
from reverse_proxy_mcp.models.database import BackendServer, ProxyRule, User
from reverse_proxy_mcp.models.schemas import MetricResponse
from reverse_proxy_mcp.services.metrics import MetricsService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
def get_health(db: Session = Depends(get_db)) -> dict:
    """Get system health status (no authentication required)."""
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        database_status = "connected"
    except Exception:
        database_status = "disconnected"

    # Count active backends and rules
    active_backends = db.query(BackendServer).filter(BackendServer.is_active).count()
    active_rules = db.query(ProxyRule).filter(ProxyRule.is_active).count()

    # Check nginx status (simplified - assumes if we're running, nginx is too)
    nginx_status = "active"

    return {
        "status": "healthy" if database_status == "connected" else "unhealthy",
        "version": settings.app_version,
        "database": database_status,
        "nginx": nginx_status,
        "active_backends": active_backends,
        "active_rules": active_rules,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@router.get("/metrics", response_model=list[MetricResponse])
def get_metrics(
    backend_id: int | None = None,
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> list[MetricResponse]:
    """Get proxy metrics.

    Args:
        backend_id: Optional backend ID to filter by
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of results (default: 100)
    """
    metrics = MetricsService.get_metrics(db, backend_id=backend_id, hours=hours, limit=limit)
    return metrics


@router.get("/metrics/summary")
def get_metrics_summary(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    """Get aggregate metrics summary.

    Args:
        hours: Number of hours to look back (default: 24)
    """
    return MetricsService.get_summary(db, hours=hours)


@router.get("/metrics/backends/{backend_id}")
def get_backend_metrics(
    backend_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    """Get metrics for a specific backend.

    Args:
        backend_id: Backend ID
        hours: Number of hours to look back (default: 24)
    """
    try:
        return MetricsService.get_backend_metrics(db, backend_id, hours=hours)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/metrics/cleanup")
def cleanup_metrics(
    days_retention: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    """Delete old metrics (admin only).

    Args:
        days_retention: Number of days to keep (default: 30)
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    deleted_count = MetricsService.cleanup_old_metrics(db, days_retention)
    return {"detail": f"Deleted {deleted_count} metrics older than {days_retention} days"}
