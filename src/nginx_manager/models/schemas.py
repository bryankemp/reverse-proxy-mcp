"""Pydantic request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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

    email: EmailStr | None = None
    role: str | None = Field(None, pattern="^(admin|user)$")
    is_active: bool | None = None


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Backend Server Schemas
class BackendServerBase(BaseModel):
    """Base backend server schema."""

    name: str = Field(..., min_length=1, max_length=255)
    ip: str = Field(..., min_length=7, max_length=45)
    port: int = Field(default=80, ge=1, le=65535)
    service_description: str | None = None


class BackendServerCreate(BackendServerBase):
    """Backend server creation schema."""

    pass


class BackendServerUpdate(BaseModel):
    """Backend server update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    ip: str | None = Field(None, min_length=7, max_length=45)
    port: int | None = Field(None, ge=1, le=65535)
    service_description: str | None = None
    is_active: bool | None = None


class BackendServerResponse(BackendServerBase):
    """Backend server response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime


# Proxy Rule Schemas
class ProxyRuleBase(BaseModel):
    """Base proxy rule schema."""

    frontend_domain: str = Field(..., min_length=5, max_length=255)
    backend_id: int
    access_control: str = Field(default="public", pattern="^(public|internal)$")
    ip_whitelist: str | None = None


class ProxyRuleCreate(ProxyRuleBase):
    """Proxy rule creation schema."""

    pass


class ProxyRuleUpdate(BaseModel):
    """Proxy rule update schema."""

    frontend_domain: str | None = Field(None, min_length=5, max_length=255)
    backend_id: int | None = None
    access_control: str | None = Field(None, pattern="^(public|internal)$")
    ip_whitelist: str | None = None
    is_active: bool | None = None


class ProxyRuleResponse(ProxyRuleBase):
    """Proxy rule response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime


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

    expiry_date: datetime | None = None


class SSLCertificateResponse(SSLCertificateBase):
    """SSL certificate response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cert_path: str
    key_path: str
    expiry_date: datetime | None = None
    uploaded_by: int | None = None
    uploaded_at: datetime
    updated_at: datetime


# Configuration Schemas
class ConfigBase(BaseModel):
    """Base configuration schema."""

    key: str = Field(..., min_length=1, max_length=100)
    value: str | None = None


class ConfigResponse(ConfigBase):
    """Configuration response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    """Audit log response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    action: str
    resource_type: str
    resource_id: str
    changes: str | None = None
    ip_address: str | None = None
    timestamp: datetime


# Metrics Schemas
class MetricResponse(BaseModel):
    """Metric response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    backend_id: int | None = None
    request_count: int
    avg_response_time: float | None = None
    error_rate: float | None = None
    status_2xx: int
    status_3xx: int
    status_4xx: int
    status_5xx: int


# Authentication Schemas
class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict | None = None


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


# Error Schemas
class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: str | None = None
    timestamp: datetime | None = None
