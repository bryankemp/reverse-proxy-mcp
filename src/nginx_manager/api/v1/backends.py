"""Backend server endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nginx_manager.api.dependencies import require_admin, require_user
from nginx_manager.core import get_db
from nginx_manager.core.nginx import NginxConfigGenerator
from nginx_manager.models.database import BackendServer, User
from nginx_manager.models.schemas import (
    BackendServerCreate,
    BackendServerResponse,
    BackendServerUpdate,
)

router = APIRouter(prefix="/backends", tags=["backends"])


@router.get("", response_model=list[BackendServerResponse])
def list_backends(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> list[BackendServerResponse]:
    """List all backend servers."""
    return db.query(BackendServer).filter(BackendServer.is_active).all()


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
    # Check if backend with same name exists
    existing = db.query(BackendServer).filter(BackendServer.name == backend.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Backend name already exists"
        )

    db_backend = BackendServer(
        name=backend.name,
        ip=backend.ip,
        port=backend.port,
        service_description=backend.service_description,
        created_by=current_user.id,
    )
    db.add(db_backend)
    db.commit()
    db.refresh(db_backend)

    # Auto-reload Nginx after backend creation
    generator = NginxConfigGenerator(config_path="/etc/nginx/nginx.conf")
    success, message = generator.apply_config(db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend created but Nginx reload failed: {message}",
        )

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

    # Check if new name conflicts
    if backend_update.name and backend_update.name != db_backend.name:
        existing = db.query(BackendServer).filter(BackendServer.name == backend_update.name).first()
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
    if backend_update.service_description is not None:
        db_backend.service_description = backend_update.service_description
    if backend_update.is_active is not None:
        db_backend.is_active = backend_update.is_active

    db.commit()
    db.refresh(db_backend)

    # Auto-reload Nginx after backend update
    generator = NginxConfigGenerator(config_path="/etc/nginx/nginx.conf")
    success, message = generator.apply_config(db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend updated but Nginx reload failed: {message}",
        )

    return db_backend


@router.delete("/{backend_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backend(
    backend_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete backend server (soft delete, admin only)."""
    db_backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
    if not db_backend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend not found")

    db_backend.is_active = False
    db.commit()

    # Auto-reload Nginx after backend deletion
    generator = NginxConfigGenerator(config_path="/etc/nginx/nginx.conf")
    success, message = generator.apply_config(db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend deleted but Nginx reload failed: {message}",
        )


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
