"""API v2 Matrix URIs for resource group filtering.

Matrix URIs provide filtered views of resources based on state and access control.
Examples:
- GET /api/v2/active-backends - Only active backends
- GET /api/v2/public-rules - Only public proxy rules
- GET /api/v2/expiring-certificates?days=30 - Certificates expiring soon
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import require_user
from reverse_proxy_mcp.core.database import get_db
from reverse_proxy_mcp.models.database import BackendServer, ProxyRule, SSLCertificate, User
from reverse_proxy_mcp.models.schemas import (
    BackendServerResponse,
    ProxyRuleResponse,
    SSLCertificateResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/v2", tags=["matrix-v2"])


@router.get("/active-backends", response_model=list[BackendServerResponse])
def get_active_backends(db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    """Get only active backend servers.

    Returns:
        List of active backends
    """
    backends = db.query(BackendServer).filter(BackendServer.is_active).all()
    return backends


@router.get("/inactive-backends", response_model=list[BackendServerResponse])
def get_inactive_backends(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
):
    """Get only inactive backend servers.

    Returns:
        List of inactive backends
    """
    backends = db.query(BackendServer).filter(~BackendServer.is_active).all()
    return backends


@router.get("/public-rules", response_model=list[ProxyRuleResponse])
def get_public_rules(db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    """Get only public proxy rules.

    Returns:
        List of public proxy rules
    """
    rules = (
        db.query(ProxyRule).filter(ProxyRule.access_control == "public", ProxyRule.is_active).all()
    )
    return rules


@router.get("/private-rules", response_model=list[ProxyRuleResponse])
def get_private_rules(db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    """Get only private proxy rules.

    Returns:
        List of private proxy rules
    """
    rules = (
        db.query(ProxyRule).filter(ProxyRule.access_control == "private", ProxyRule.is_active).all()
    )
    return rules


@router.get("/ssl-enabled-rules", response_model=list[ProxyRuleResponse])
def get_ssl_enabled_rules(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
):
    """Get only SSL-enabled proxy rules.

    Returns:
        List of SSL-enabled proxy rules
    """
    rules = db.query(ProxyRule).filter(ProxyRule.ssl_enabled, ProxyRule.is_active).all()
    return rules


@router.get("/expiring-certificates", response_model=list[SSLCertificateResponse])
def get_expiring_certificates(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Get certificates expiring within specified days.

    Args:
        days: Number of days to look ahead (default: 30)

    Returns:
        List of expiring certificates
    """
    threshold = datetime.now(UTC) + timedelta(days=days)
    certificates = db.query(SSLCertificate).filter(SSLCertificate.expiry_date <= threshold).all()
    return certificates


@router.get("/default-certificates", response_model=list[SSLCertificateResponse])
def get_default_certificates(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
):
    """Get all default certificates.

    Returns:
        List of default certificates
    """
    certificates = db.query(SSLCertificate).filter(SSLCertificate.is_default).all()
    return certificates


@router.get("/active-users", response_model=list[UserResponse])
def get_active_users(db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    """Get only active users.

    Returns:
        List of active users
    """
    users = db.query(User).filter(User.is_active).all()
    return users


@router.get("/admin-users", response_model=list[UserResponse])
def get_admin_users(db: Session = Depends(get_db), current_user: User = Depends(require_user)):
    """Get only admin users.

    Returns:
        List of admin users
    """
    users = db.query(User).filter(User.role == "admin", User.is_active).all()
    return users


@router.get("/backends-by-protocol/{protocol}", response_model=list[BackendServerResponse])
def get_backends_by_protocol(
    protocol: str, db: Session = Depends(get_db), current_user: User = Depends(require_user)
):
    """Get backends filtered by protocol.

    Args:
        protocol: Backend protocol (http or https)

    Returns:
        List of backends with specified protocol
    """
    backends = (
        db.query(BackendServer)
        .filter(BackendServer.protocol == protocol, BackendServer.is_active)
        .all()
    )
    return backends


@router.get("/rules-by-backend/{backend_id}", response_model=list[ProxyRuleResponse])
def get_rules_by_backend(
    backend_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)
):
    """Get all proxy rules for a specific backend.

    Args:
        backend_id: Backend server ID

    Returns:
        List of proxy rules using the backend
    """
    rules = db.query(ProxyRule).filter(ProxyRule.backend_id == backend_id).all()
    return rules


@router.get("/rules-by-certificate/{certificate_id}", response_model=list[ProxyRuleResponse])
def get_rules_by_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Get all proxy rules using a specific certificate.

    Args:
        certificate_id: SSL certificate ID

    Returns:
        List of proxy rules using the certificate
    """
    rules = db.query(ProxyRule).filter(ProxyRule.certificate_id == certificate_id).all()
    return rules
