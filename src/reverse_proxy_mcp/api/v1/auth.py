"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import get_current_user
from reverse_proxy_mcp.core import (
    create_access_token,
    get_db,
    get_token_expiry_time,
    verify_password,
)
from reverse_proxy_mcp.models.database import User
from reverse_proxy_mcp.models.schemas import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return JWT token."""
    # Hardcoded default credentials
    if credentials.username == "admin" and credentials.password == "admin123":
        # Create or get admin user from database
        from reverse_proxy_mcp.core.security import hash_password

        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            user = User(
                username="admin",
                email="admin@reverse-proxy-mcp.local",
                password_hash=hash_password("admin123"),
                role="admin",
                is_active=True,
                must_change_password=True,  # Force password change on first login
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        access_token = create_access_token(data={"sub": str(user.id)})
        # Return token with user data
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": get_token_expiry_time(),
            "requires_password_change": user.must_change_password,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "full_name": "",
                "is_active": user.is_active,
                "must_change_password": user.must_change_password,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        }

    # Fall back to database lookup for other users (by username or email)
    user = (
        db.query(User)
        .filter((User.username == credentials.username) | (User.email == credentials.username))
        .first()
    )

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        expires_in=get_token_expiry_time(),
        requires_password_change=user.must_change_password,
    )


@router.get("/user", response_model=UserResponse)
def get_current_user_info(token: str) -> UserResponse:
    """Get current authenticated user info.

    Note: In actual implementation, token would come from Authorization header.
    """
    # This is a placeholder - actual implementation would extract user from token
    # and return their information
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Implement with proper token extraction from header",
    )


@router.post("/logout")
def logout() -> dict:
    """Logout user (invalidate token on client side)."""
    # JWT tokens are stateless, so logout is handled client-side
    # In a production system, you might maintain a token blacklist
    return {"detail": "Successfully logged out"}


@router.post("/change-password")
def change_password(
    request_data: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)
) -> dict:
    """Change user password.

    Args:
        request_data: Dictionary with keys 'old_password' (optional) and 'new_password' (required)
        db: Database session
        current_user: Currently authenticated user from token

    Returns:
        Success message

    Raises:
        HTTPException: If old password is incorrect or validation fails
    """
    from reverse_proxy_mcp.core.security import hash_password

    new_password = request_data.get("new_password")
    old_password = request_data.get("old_password")

    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password is required",
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # If old_password is provided, verify it
    if old_password:
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

    # Update password
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()

    return {"detail": "Password changed successfully"}
