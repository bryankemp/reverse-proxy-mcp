"""User management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nginx_manager.api.dependencies import require_admin, require_user
from nginx_manager.core import get_db, hash_password
from nginx_manager.models.database import User
from nginx_manager.models.schemas import UserCreate, UserResponse, UserUpdate
from nginx_manager.services.audit import AuditService
from nginx_manager.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
) -> List[UserResponse]:
    """List all users (admin only)."""
    return UserService.get_all_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> UserResponse:
    """Get user details (admin or self)."""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Allow users to view their own profile
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """Create new user (admin only)."""
    # Check if username already exists
    existing = UserService.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )

    # Create user
    new_user = UserService.create_user(db, user)

    # Audit log
    AuditService.log_user_created(db, current_user, new_user)

    return new_user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> UserResponse:
    """Update user (admin or self)."""
    try:
        updated_user = UserService.update_user(db, user_id, user_update, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Audit log
    AuditService.log_user_updated(db, current_user, user_id, user_update.model_dump())

    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete user (admin only - soft delete)."""
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Audit log
    AuditService.log_user_deleted(db, current_user, user_id)


@router.post("/{user_id}/change-password")
def change_password(
    user_id: int,
    old_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    """Change password (user or admin)."""
    # Allow users to change their own password, admins can change anyone's
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    success = UserService.change_password(db, user_id, old_password, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    # Audit log
    AuditService.log_action(
        db, current_user, "updated", "user_password", str(user_id), {"changed": True}
    )

    return {"detail": "Password changed successfully"}
