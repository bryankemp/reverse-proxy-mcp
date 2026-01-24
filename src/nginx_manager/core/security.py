"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from nginx_manager.core.config import settings


def hash_password(password: str) -> str:
    \"\"\"Hash a password using bcrypt.\"\"\"
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    \"\"\"Create a JWT access token.\"\"\"
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    \"\"\"Decode and validate a JWT token.\"\"\"
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def get_token_expiry_time() -> int:
    \"\"\"Get token expiry time in seconds.\"\"\"
    return settings.access_token_expire_minutes * 60
