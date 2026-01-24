"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(default="user", pattern="^(admin|user)$")


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Backend Server Schemas
class BackendServerBase(BaseModel):
    """Base backend server schema."""

    name: str = Field(..., min_length=1, max_length=255)
    ip: str = Field(..., min_length=7, max_length=45)
    port: int = Field(default=80, ge=1, le=65535)
    service_description: Optional[str] = None


class BackendServerCreate(BackendServerBase):
    """Backend server creation schema."""

    pass


class BackendServerUpdate(BaseModel):
    """Backend server update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    ip: Optional[str] = Field(None, min_length=7, max_length=45)
    port: Optional[int] = Field(None, ge=1, le=65535)
    service_description: Optional[str] = None
    is_active: Optional[bool] = None


class BackendServerResponse(BackendServerBase):
    """Backend server response schema."""

    id: int
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Proxy Rule Schemas
class ProxyRuleBase(BaseModel):
    """Base proxy rule schema."""

    frontend_domain: str = Field(..., min_length=5, max_length=255)
    backend_id: int
    access_control: str = Field(default="public", pattern="^(public|internal)$")
    ip_whitelist: Optional[str] = None


class ProxyRuleCreate(ProxyRuleBase):
    """Proxy rule creation schema."""

    pass


class ProxyRuleUpdate(BaseModel):
    """Proxy rule update schema."""

    frontend_domain: Optional[str] = Field(None, min_length=5, max_length=255)
    backend_id: Optional[int] = None
    access_control: Optional[str] = Field(None, pattern="^(public|internal)$")
    ip_whitelist: Optional[str] = None
    is_active: Optional[bool] = None


class ProxyRuleResponse(ProxyRuleBase):
    """Proxy rule response schema."""

    id: int
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# SSL Certificate Schemas
class SSLCertificateBase(BaseModel):
    """Base SSL certificate schema."""

    domain: str = Field(..., min_length=5, max_length=255)


class SSLCertificateCreate(BaseModel):
    """SSL certificate creation schema."""

    domain: str = Field(..., min_length=5, max_length=255)
    cert_file: str  # File content (base64 or raw)
    key_file: str  # File content (base64 or raw)


class SSLCertificateUpdate(BaseModel):
    """SSL certificate update schema."""

    expiry_date: Optional[datetime] = None


class SSLCertificateResponse(SSLCertificateBase):
    """SSL certificate response schema."""

    id: int
    cert_path: str
    key_path: str
    expiry_date: Optional[datetime] = None
    uploaded_by: Optional[int] = None
    uploaded_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Configuration Schemas
class ConfigBase(BaseModel):
    """Base configuration schema."""

    key: str = Field(..., min_length=1, max_length=100)
    value: Optional[str] = None


class ConfigResponse(ConfigBase):
    """Configuration response schema."""

    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    """Audit log response schema."""

    id: int
    user_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: str
    changes: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Metrics Schemas
class MetricResponse(BaseModel):
    """Metric response schema."""

    id: int
    timestamp: datetime
    backend_id: Optional[int] = None
    request_count: int
    avg_response_time: Optional[float] = None
    error_rate: Optional[float] = None
    status_2xx: int
    status_3xx: int
    status_4xx: int
    status_5xx: int

    class Config:
        from_attributes = True


# Authentication Schemas
class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


# Error Schemas
class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: Optional[str] = None
    timestamp: Optional[datetime] = None
