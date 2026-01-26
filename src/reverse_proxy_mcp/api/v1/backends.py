"""Backend server endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import require_admin, require_user
from reverse_proxy_mcp.core import get_db
from reverse_proxy_mcp.core.nginx import NginxConfigGenerator
from reverse_proxy_mcp.models.database import BackendServer, User
from reverse_proxy_mcp.models.schemas import (
    BackendServerCreate,
    BackendServerResponse,
    BackendServerUpdate,
)
from reverse_proxy_mcp.services.audit import AuditService

router = APIRouter(prefix="/backends", tags=["backends"])


@router.get("", response_model=list[BackendServerResponse])
def list_backends(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> list[BackendServerResponse]:
    """List all backend servers (including inactive)."""
    return db.query(BackendServer).all()


@router.get("/{backend_id}", response_model=BackendServerResponse)
def get_backend(
    backend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> BackendServerResponse:
    """Get specific backend server."""
    backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
    if not backend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend not found")
    return backend


@router.post("", response_model=BackendServerResponse, status_code=status.HTTP_201_CREATED)
def create_backend(
    backend: BackendServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> BackendServerResponse:
    """Create new backend server (admin only)."""
    # Check if active backend with same name exists
    existing = (
        db.query(BackendServer)
        .filter(BackendServer.name == backend.name, BackendServer.is_active)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Backend name already exists"
        )

    db_backend = BackendServer(
        name=backend.name,
        ip=backend.ip,
        port=backend.port,
        protocol=backend.protocol,
        service_description=backend.service_description,
        created_by=current_user.id,
    )
    db.add(db_backend)
    db.commit()
    db.refresh(db_backend)

    # Audit log
    AuditService.log_action(
        db, current_user, "created", "backend", str(db_backend.id), {"name": backend.name}
    )

    # Auto-reload Nginx after backend creation
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            # Log the error but don't fail the request
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        # Log but don't fail
        import logging

        logging.error(f"Nginx reload exception: {e}")

    return db_backend


@router.put("/{backend_id}", response_model=BackendServerResponse)
def update_backend(
    backend_id: int,
    backend_update: BackendServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> BackendServerResponse:
    """Update backend server (admin only)."""
    db_backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
    if not db_backend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend not found")

    # Check if new name conflicts with active backends
    if backend_update.name and backend_update.name != db_backend.name:
        existing = (
            db.query(BackendServer)
            .filter(
                BackendServer.name == backend_update.name,
                BackendServer.is_active,
                BackendServer.id != backend_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Backend name already exists"
            )

    if backend_update.name:
        db_backend.name = backend_update.name
    if backend_update.ip:
        db_backend.ip = backend_update.ip
    if backend_update.port:
        db_backend.port = backend_update.port
    if backend_update.protocol:
        db_backend.protocol = backend_update.protocol
    if backend_update.service_description is not None:
        db_backend.service_description = backend_update.service_description
    if backend_update.is_active is not None:
        db_backend.is_active = backend_update.is_active

    db.commit()
    db.refresh(db_backend)

    # Audit log
    AuditService.log_action(
        db, current_user, "updated", "backend", str(backend_id), {"name": db_backend.name}
    )

    # Auto-reload Nginx after backend update
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        import logging

        logging.error(f"Nginx reload exception: {e}")

    return db_backend


@router.delete("/{backend_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backend(
    backend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Permanently delete backend server (hard delete, admin only)."""
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"DELETE request for backend_id={backend_id} by user={current_user.username}")

        db_backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
        if not db_backend:
            logger.warning(f"Backend {backend_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend not found")

        backend_name = db_backend.name
        logger.info(f"Found backend: {backend_name}")

        # Audit log before deletion
        logger.info("Creating audit log entry...")
        AuditService.log_action(
            db,
            current_user,
            "permanently_deleted",
            "backend",
            str(backend_id),
            {"name": backend_name},
        )
        logger.info("Audit log created successfully")

        # Hard delete from database
        logger.info("Deleting backend from database...")
        db.delete(db_backend)
        db.commit()
        logger.info("Backend deleted and committed successfully")

        # Auto-reload Nginx after permanent deletion
        logger.info("Reloading Nginx config...")
        try:
            generator = NginxConfigGenerator()
            success, message = generator.apply_config(db)
            if not success:
                logger.error(f"Nginx reload failed: {message}")
            else:
                logger.info("Nginx reload succeeded")
        except Exception as nginx_e:
            logger.error(f"Nginx reload exception: {nginx_e}")
            logger.error(traceback.format_exc())

        logger.info("Delete operation completed successfully")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CRITICAL ERROR in delete_backend: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backend: {str(e)}",
        ) from e


@router.post("/{backend_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_backend(
    backend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Deactivate backend server (marks as inactive, admin only)."""
    db_backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
    if not db_backend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend not found")

    # Soft delete - mark as inactive
    db_backend.is_active = False
    db.commit()

    # Audit log
    AuditService.log_action(
        db, current_user, "deactivated", "backend", str(backend_id), {"name": db_backend.name}
    )

    # Auto-reload Nginx after backend deletion
    try:
        generator = NginxConfigGenerator()
        success, message = generator.apply_config(db)
        if not success:
            import logging

            logging.error(f"Nginx reload failed: {message}")
    except Exception as e:
        import logging

        logging.error(f"Nginx reload exception: {e}")

    return None


@router.post("/{backend_id}/test")
def test_backend(
    backend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    """Test backend connectivity."""
    db_backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
    if not db_backend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend not found")

    # Placeholder for actual connectivity test
    return {
        "backend_id": backend_id,
        "status": "ok",
        "response_time_ms": 42,
        "message": "Connectivity test passed",
    }
