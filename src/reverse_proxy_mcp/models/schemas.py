"""Pydantic request and response schemas."""

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


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
    protocol: str = Field(default="http", pattern="^(http|https)$")
    service_description: str | None = None


class BackendServerCreate(BackendServerBase):
    """Backend server creation schema."""

    pass


class BackendServerUpdate(BaseModel):
    """Backend server update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    ip: str | None = Field(None, min_length=7, max_length=45)
    port: int | None = Field(None, ge=1, le=65535)
    protocol: str | None = Field(None, pattern="^(http|https)$")
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
    certificate_id: int | None = None  # NULL = use default certificate
    access_control: str = Field(default="public", pattern="^(public|internal)$")
    ip_whitelist: str | None = None

    # Security settings
    enable_hsts: bool = False
    hsts_max_age: int = Field(default=31536000, ge=0)
    enable_security_headers: bool = True
    custom_headers: str | None = None  # JSON string
    rate_limit: str | None = Field(None, pattern=r"^\d+r/[smh]$")  # e.g. "100r/s"
    ssl_enabled: bool = True
    force_https: bool = True


class ProxyRuleCreate(ProxyRuleBase):
    """Proxy rule creation schema."""

    pass


class ProxyRuleUpdate(BaseModel):
    """Proxy rule update schema."""

    frontend_domain: str | None = Field(None, min_length=5, max_length=255)
    backend_id: int | None = None
    certificate_id: int | None = None
    access_control: str | None = Field(None, pattern="^(public|internal)$")
    ip_whitelist: str | None = None
    is_active: bool | None = None

    # Security settings
    enable_hsts: bool | None = None
    hsts_max_age: int | None = Field(None, ge=0)
    enable_security_headers: bool | None = None
    custom_headers: str | None = None
    rate_limit: str | None = Field(None, pattern=r"^\d+r/[smh]$")
    ssl_enabled: bool | None = None
    force_https: bool | None = None


class ProxyRuleResponse(ProxyRuleBase):
    """Proxy rule response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
    certificate_name: str | None = None  # Populated from join with certificates table

    # Inherited from ProxyRuleBase:
    # certificate_id, enable_hsts, hsts_max_age, enable_security_headers,
    # custom_headers, rate_limit, ssl_enabled, force_https


# SSL Certificate Schemas
class SSLCertificateBase(BaseModel):
    """Base SSL certificate schema."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Friendly name for certificate"
    )
    domain: str = Field(
        ..., min_length=1, max_length=255, description="Domain pattern (e.g., *.example.com)"
    )


class SSLCertificateCreate(BaseModel):
    """SSL certificate creation schema (used with multipart form)."""

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    is_default: bool = False


class SSLCertificateUpdate(BaseModel):
    """SSL certificate update schema."""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_default: bool | None = None


class SSLCertificateResponse(SSLCertificateBase):
    """SSL certificate response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cert_path: str
    key_path: str
    certificate_type: str
    is_default: bool
    expiry_date: datetime | None = None
    uploaded_by: int | None = None
    uploaded_at: datetime
    updated_at: datetime


class CertificateListItem(BaseModel):
    """Simplified certificate info for dropdowns."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str
    is_default: bool
    expiry_date: datetime | None = None


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

    username: str = Field(
        ...,
        min_length=3,
        description="Username or email",
        validation_alias=AliasChoices("username", "email"),
    )
    password: str = Field(..., min_length=8)


# Error Schemas
class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: str | None = None
    timestamp: datetime | None = None
