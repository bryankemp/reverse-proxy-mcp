"""SSL certificate management endpoints."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from reverse_proxy_mcp.api.dependencies import require_admin, require_user
from reverse_proxy_mcp.core import get_db
from reverse_proxy_mcp.models.database import User
from reverse_proxy_mcp.models.schemas import CertificateListItem, SSLCertificateResponse
from reverse_proxy_mcp.services.audit import AuditService
from reverse_proxy_mcp.services.certificate import CertificateService

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("", response_model=list[SSLCertificateResponse])
def list_certificates(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> list[SSLCertificateResponse]:
    """List all SSL certificates."""
    return CertificateService.get_all_certificates(db)


@router.get("/dropdown", response_model=list[CertificateListItem])
def list_certificates_for_dropdown(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> list[CertificateListItem]:
    """List certificates in simplified format for UI dropdowns."""
    return CertificateService.get_all_certificates(db)


@router.get("/{cert_id}", response_model=SSLCertificateResponse)
def get_certificate(
    cert_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> SSLCertificateResponse:
    """Get certificate details by ID."""
    from reverse_proxy_mcp.models.database import SSLCertificate

    cert = db.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return cert


@router.post("", response_model=SSLCertificateResponse, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    name: str = Form(...),
    domain: str = Form(...),
    is_default: bool = Form(False),
    cert_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SSLCertificateResponse:
    """Upload SSL certificate (admin only).

    Args:
        name: Friendly name for certificate (e.g., "Wildcard Kempville")
        domain: Domain pattern (e.g., "*.kempville.com" or "api.example.com")
        is_default: Whether to set as default certificate
        cert_file: PEM-encoded certificate file
        key_file: PEM-encoded private key file
    """
    from reverse_proxy_mcp.models.database import SSLCertificate

    # Check if certificate name already exists
    existing = db.query(SSLCertificate).filter(SSLCertificate.name == name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certificate with name '{name}' already exists",
        )

    try:
        # Read certificate content
        cert_content = await cert_file.read()
        if isinstance(cert_content, bytes):
            cert_content = cert_content.decode("utf-8")

        # Read key content
        key_content = await key_file.read()
        if isinstance(key_content, bytes):
            key_content = key_content.decode("utf-8")

        # Create certificate (validation happens inside)
        new_cert = CertificateService.create_certificate(
            db, name, domain, cert_content, key_content, current_user.id, is_default
        )

        # Audit log
        AuditService.log_action(
            db,
            current_user,
            "uploaded",
            "certificate",
            str(new_cert.id),
            {"name": name, "domain": domain, "is_default": is_default},
        )

        return new_cert
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload certificate: {str(e)}",
        ) from e


@router.put("/{cert_id}/set-default", response_model=SSLCertificateResponse)
def set_default_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SSLCertificateResponse:
    """Set certificate as default (admin only)."""
    try:
        cert = CertificateService.set_default_certificate(db, cert_id)

        # Audit log
        AuditService.log_action(
            db, current_user, "updated", "certificate", str(cert_id), {"is_default": True}
        )

        return cert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete certificate by ID (admin only)."""
    from reverse_proxy_mcp.models.database import SSLCertificate

    cert = db.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    success = CertificateService.delete_certificate(db, cert.domain)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete certificate"
        )

    # Audit log
    AuditService.log_action(
        db, current_user, "deleted", "certificate", str(cert_id), {"name": cert.name}
    )


@router.get("/{domain}/expiry-status")
def check_certificate_expiry(
    domain: str, db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> dict:
    """Check certificate expiry status."""
    from datetime import datetime

    cert = CertificateService.get_certificate_by_domain(db, domain)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    if not cert.expiry_date:
        return {"domain": domain, "status": "unknown", "days_until_expiry": None}

    days_until = (cert.expiry_date - datetime.utcnow()).days
    status_text = "expired"

    if days_until > 30:
        status_text = "valid"
    elif days_until > 0:
        status_text = "expiring_soon"

    return {
        "domain": domain,
        "status": status_text,
        "expiry_date": cert.expiry_date,
        "days_until_expiry": max(0, days_until),
    }


@router.get("/expiring/list")
def list_expiring_certificates(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
) -> dict:
    """List certificates expiring within specified days."""
    certs = CertificateService.get_expiring_certificates(db, days)
    return {
        "days_until_expiry": days,
        "count": len(certs),
        "certificates": [
            {
                "domain": cert.domain,
                "expiry_date": cert.expiry_date,
                "days_remaining": (
                    (cert.expiry_date - __import__("datetime").datetime.utcnow()).days
                    if cert.expiry_date
                    else None
                ),
            }
            for cert in certs
        ],
    }
