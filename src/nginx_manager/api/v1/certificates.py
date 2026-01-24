"""SSL certificate management endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from nginx_manager.api.dependencies import require_admin, require_user
from nginx_manager.core import get_db
from nginx_manager.models.database import User
from nginx_manager.models.schemas import SSLCertificateResponse
from nginx_manager.services.audit import AuditService
from nginx_manager.services.certificate import CertificateService

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("", response_model=list[SSLCertificateResponse])
def list_certificates(
    db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> list[SSLCertificateResponse]:
    """List all SSL certificates."""
    return CertificateService.get_all_certificates(db)


@router.get("/{domain}", response_model=SSLCertificateResponse)
def get_certificate(
    domain: str, db: Session = Depends(get_db), current_user: User = Depends(require_user)
) -> SSLCertificateResponse:
    """Get certificate details."""
    cert = CertificateService.get_certificate_by_domain(db, domain)
    if not cert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return cert


@router.post("", response_model=SSLCertificateResponse, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    domain: str,
    cert_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> SSLCertificateResponse:
    """Upload SSL certificate (admin only)."""
    # Check if certificate already exists
    existing = CertificateService.get_certificate_by_domain(db, domain)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Certificate for this domain already exists",
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

        # Create certificate
        new_cert = CertificateService.create_certificate(
            db, domain, cert_content, key_content, current_user.id
        )

        # Audit log
        AuditService.log_action(
            db, current_user, "uploaded", "certificate", domain, {"domain": domain}
        )

        return new_cert
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid certificate: {str(e)}",
        ) from e


@router.delete("/{domain}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Delete certificate (admin only)."""
    success = CertificateService.delete_certificate(db, domain)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    # Audit log
    AuditService.log_action(db, current_user, "deleted", "certificate", domain)


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
