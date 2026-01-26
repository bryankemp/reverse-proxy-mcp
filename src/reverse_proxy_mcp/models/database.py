"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin or user
    is_active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)  # Force password change on first login
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_backends = relationship(
        "BackendServer", back_populates="created_by_user", foreign_keys="BackendServer.created_by"
    )
    created_rules = relationship(
        "ProxyRule", back_populates="created_by_user", foreign_keys="ProxyRule.created_by"
    )
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class BackendServer(Base):
    """Backend server model."""

    __tablename__ = "backend_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    ip = Column(String(45), nullable=False)  # IPv4 or IPv6
    port = Column(Integer, nullable=False, default=80)
    protocol = Column(String(10), nullable=False, default="http")  # http or https
    service_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User", back_populates="created_backends")
    proxy_rules = relationship("ProxyRule", back_populates="backend")

    __table_args__ = (UniqueConstraint("ip", "port", name="uq_backend_ip_port"),)

    def __repr__(self) -> str:
        return f"<BackendServer(id={self.id}, name={self.name}, ip={self.ip}:{self.port})>"


class ProxyRule(Base):
    """Proxy routing rule model."""

    __tablename__ = "proxy_rules"

    id = Column(Integer, primary_key=True, index=True)
    frontend_domain = Column(String(255), unique=True, index=True, nullable=False)
    backend_id = Column(Integer, ForeignKey("backend_servers.id"), nullable=False)
    certificate_id = Column(
        Integer, ForeignKey("ssl_certificates.id"), nullable=True
    )  # NULL = use default
    access_control = Column(String(20), nullable=False, default="public")  # public or internal
    ip_whitelist = Column(Text, nullable=True)  # JSON list of allowed IPs
    is_active = Column(Boolean, default=True)

    # Security settings
    enable_hsts = Column(Boolean, default=False)
    hsts_max_age = Column(Integer, default=31536000)  # 1 year in seconds
    enable_security_headers = Column(Boolean, default=True)
    custom_headers = Column(Text, nullable=True)  # JSON key-value pairs
    rate_limit = Column(String(50), nullable=True)  # e.g. "100r/s"
    ssl_enabled = Column(Boolean, default=True)
    force_https = Column(Boolean, default=True)  # HTTP to HTTPS redirect

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    backend = relationship("BackendServer", back_populates="proxy_rules")
    certificate = relationship("SSLCertificate", back_populates="proxy_rules")
    created_by_user = relationship("User", back_populates="created_rules")

    def __repr__(self) -> str:
        return (
            f"<ProxyRule(id={self.id}, domain={self.frontend_domain}, "
            f"backend_id={self.backend_id})>"
        )


class SSLCertificate(Base):
    """SSL certificate model."""

    __tablename__ = "ssl_certificates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)  # Friendly name
    domain = Column(String(255), index=True, nullable=False)  # Can be wildcard like *.example.com
    cert_path = Column(String(500), nullable=False)
    key_path = Column(String(500), nullable=False)
    is_default = Column(
        Boolean, default=False, nullable=False
    )  # Default cert for unmatched domains
    certificate_type = Column(String(20), nullable=False)  # wildcard or domain-specific
    expiry_date = Column(DateTime, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    proxy_rules = relationship("ProxyRule", back_populates="certificate")

    def __repr__(self) -> str:
        return (
            f"<SSLCertificate(name={self.name}, domain={self.domain}, default={self.is_default})>"
        )


class AuditLog(Base):
    """Audit log model for tracking changes."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # created, updated, deleted
    resource_type = Column(String(50), nullable=False)  # user, backend, rule, cert, config
    resource_id = Column(String(255), nullable=False)
    changes = Column(Text, nullable=True)  # JSON with before/after values
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action}, "
            f"resource={self.resource_type}:{self.resource_id})>"
        )


class ProxyConfig(Base):
    """Global proxy configuration model."""

    __tablename__ = "proxy_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ProxyConfig(key={self.key}, value={self.value})>"


class Metric(Base):
    """Metrics model for tracking proxy performance."""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    backend_id = Column(Integer, ForeignKey("backend_servers.id"), nullable=True, index=True)
    request_count = Column(Integer, default=0)
    avg_response_time = Column(Float, nullable=True)  # milliseconds
    error_rate = Column(Float, nullable=True)  # percentage
    status_2xx = Column(Integer, default=0)
    status_3xx = Column(Integer, default=0)
    status_4xx = Column(Integer, default=0)
    status_5xx = Column(Integer, default=0)

    def __repr__(self) -> str:
        return (
            f"<Metric(timestamp={self.timestamp}, backend_id={self.backend_id}, "
            f"requests={self.request_count})>"
        )
