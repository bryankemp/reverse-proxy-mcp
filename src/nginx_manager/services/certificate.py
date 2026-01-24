"""SSL certificate management service."""

import os
from datetime import datetime
from typing import Optional

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from sqlalchemy.orm import Session

from nginx_manager.core.config import settings
from nginx_manager.models.database import SSLCertificate


class CertificateService:
    """Service for managing SSL certificates."""

    @staticmethod
    def parse_certificate_expiry(cert_content: str) -> Optional[datetime]:
        """Parse certificate and extract expiry date.
        
        Args:
            cert_content: PEM-encoded certificate content
            
        Returns:
            Expiry datetime or None if parsing fails
        """
        try:
            cert = x509.load_pem_x509_certificate(
                cert_content.encode(), default_backend()
            )
            expiry = cert.not_valid_after()
            return datetime.fromisoformat(expiry.isoformat())
        except Exception:
            return None

    @staticmethod
    def save_certificate_files(
        domain: str, cert_content: str, key_content: str
    ) -> tuple[str, str]:
        """Save certificate and key files to disk.
        
        Args:
            domain: Certificate domain name
            cert_content: PEM-encoded certificate
            key_content: PEM-encoded private key
            
        Returns:
            Tuple of (cert_path, key_path)
            
        Raises:
            IOError: If file writing fails
        """
        os.makedirs(settings.certs_path, exist_ok=True)

        cert_path = os.path.join(settings.certs_path, f"{domain}.crt")
        key_path = os.path.join(settings.certs_path, f"{domain}.key")

        with open(cert_path, "w") as f:
            f.write(cert_content)
        os.chmod(cert_path, 0o644)

        with open(key_path, "w") as f:
            f.write(key_content)
        os.chmod(key_path, 0o600)  # Restrict key permissions

        return cert_path, key_path

    @staticmethod
    def create_certificate(
        db: Session, domain: str, cert_content: str, key_content: str, user_id: int
    ) -> SSLCertificate:
        """Create and store a new certificate.
        
        Args:
            db: Database session
            domain: Certificate domain
            cert_content: PEM-encoded certificate
            key_content: PEM-encoded private key
            user_id: ID of user uploading certificate
            
        Returns:
            Created certificate record
        """
        # Parse expiry date
        expiry_date = CertificateService.parse_certificate_expiry(cert_content)

        # Save files to disk
        cert_path, key_path = CertificateService.save_certificate_files(
            domain, cert_content, key_content
        )

        # Create database record
        db_cert = SSLCertificate(
            domain=domain,
            cert_path=cert_path,
            key_path=key_path,
            expiry_date=expiry_date,
            uploaded_by=user_id,
        )
        db.add(db_cert)
        db.commit()
        db.refresh(db_cert)
        return db_cert

    @staticmethod
    def get_certificate_by_domain(db: Session, domain: str) -> Optional[SSLCertificate]:
        """Get certificate by domain.
        
        Args:
            db: Database session
            domain: Certificate domain
            
        Returns:
            Certificate record or None
        """
        return db.query(SSLCertificate).filter(SSLCertificate.domain == domain).first()

    @staticmethod
    def get_all_certificates(db: Session) -> list[SSLCertificate]:
        """Get all certificates."""
        return db.query(SSLCertificate).all()

    @staticmethod
    def delete_certificate(db: Session, domain: str) -> bool:
        """Delete certificate and its files.
        
        Args:
            db: Database session
            domain: Certificate domain
            
        Returns:
            True if deleted, False if not found
        """
        cert = CertificateService.get_certificate_by_domain(db, domain)
        if not cert:
            return False

        # Delete files
        if os.path.exists(cert.cert_path):
            os.remove(cert.cert_path)
        if os.path.exists(cert.key_path):
            os.remove(cert.key_path)

        # Delete database record
        db.delete(cert)
        db.commit()
        return True

    @staticmethod
    def get_expiring_certificates(
        db: Session, days_until_expiry: int = 30
    ) -> list[SSLCertificate]:
        """Get certificates expiring within specified days.
        
        Args:
            db: Database session
            days_until_expiry: Number of days to check ahead
            
        Returns:
            List of expiring certificates
        """
        from sqlalchemy import and_

        cutoff_date = datetime.utcnow() + __import__("datetime").timedelta(
            days=days_until_expiry
        )

        return (
            db.query(SSLCertificate)
            .filter(
                and_(
                    SSLCertificate.expiry_date.isnot(None),
                    SSLCertificate.expiry_date <= cutoff_date,
                )
            )
            .all()
        )
