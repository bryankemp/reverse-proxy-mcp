"""User management service."""

from typing import Optional

from sqlalchemy.orm import Session

from nginx_manager.core.security import hash_password, verify_password
from nginx_manager.models.database import User
from nginx_manager.models.schemas import UserCreate, UserUpdate


class UserService:
    """Service for managing users."""

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user."""
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            password_hash=hash_password(user_create.password),
            role=user_create.role,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_all_users(db: Session) -> list[User]:
        """Get all users."""
        return db.query(User).all()

    @staticmethod
    def update_user(
        db: Session, user_id: int, user_update: UserUpdate, current_user: User
    ) -> Optional[User]:
        """Update user (with role protection)."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        # Prevent non-admins from modifying others, and prevent changing own role
        if current_user.role != "admin" and current_user.id != user_id:
            raise PermissionError("Cannot modify other users")

        if (
            user_update.role
            and user_update.role != user.role
            and current_user.role != "admin"
        ):
            raise PermissionError("Only admins can change roles")

        if user_update.email:
            user.email = user_update.email
        if user_update.role and current_user.role == "admin":
            user.role = user_update.role
        if user_update.is_active is not None and current_user.role == "admin":
            user.is_active = user_update.is_active

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(
        db: Session, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        if not verify_password(old_password, user.password_hash):
            return False

        user.password_hash = hash_password(new_password)
        db.commit()
        return True

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete user (soft delete by deactivating)."""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = False
        db.commit()
        return True
