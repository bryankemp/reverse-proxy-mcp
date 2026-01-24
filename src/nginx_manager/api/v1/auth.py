"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nginx_manager.core import (
    create_access_token,
    get_db,
    get_token_expiry_time,
    verify_password,
)
from nginx_manager.models.database import User
from nginx_manager.models.schemas import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.username == credentials.username).first()

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

    access_token = create_access_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token, expires_in=get_token_expiry_time()
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
    old_password: str, new_password: str, token: str
) -> dict:
    """Change user password."""
    # Placeholder - implement with proper token extraction and user lookup
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Implement with proper token extraction",
    )
