"""SSL certificate management service."""

import logging
import os
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from sqlalchemy.orm import Session

from reverse_proxy_mcp.core.config import settings
from reverse_proxy_mcp.models.database import ProxyRule, SSLCertificate

logger = logging.getLogger(__name__)


class CertificateService:
    """Service for managing SSL certificates."""

    @staticmethod
    def validate_certificate_pair(cert_content: str, key_content: str) -> bool:
        """Validate that certificate and private key match.

        Args:
            cert_content: PEM-encoded certificate (may include chain)
            key_content: PEM-encoded private key

        Returns:
            True if cert/key pair is valid and matches

        Raises:
            ValueError: If certificate or key is invalid
        """
        try:
            # Load private key first
            private_key = serialization.load_pem_private_key(
                key_content.encode(), password=None, backend=default_backend()
            )

            # If cert_content contains multiple certificates (a chain),
            # extract the first one (the leaf/server certificate)
            cert_lines = cert_content.strip().split("\n")
            cert_start = None
            cert_end = None

            for i, line in enumerate(cert_lines):
                if "-----BEGIN CERTIFICATE-----" in line:
                    cert_start = i
                elif "-----END CERTIFICATE-----" in line and cert_start is not None:
                    cert_end = i
                    break

            if cert_start is None or cert_end is None:
                raise ValueError("No valid certificate found in content")

            # Extract just the first certificate
            first_cert_content = "\n".join(cert_lines[cert_start : cert_end + 1])

            # Load the first certificate
            cert = x509.load_pem_x509_certificate(first_cert_content.encode(), default_backend())

            # Verify the key matches the certificate by checking public key
            cert_public_key = cert.public_key()
            key_public_key = private_key.public_key()

            logger.info(f"Certificate public key type: {type(cert_public_key).__name__}")
            logger.info(f"Private key type: {type(private_key).__name__}")
            logger.info(f"Private key public key type: {type(key_public_key).__name__}")

            # Compare public key numbers based on key type
            if isinstance(private_key, rsa.RSAPrivateKey):
                # RSA key comparison
                if not isinstance(cert_public_key, rsa.RSAPublicKey):
                    raise ValueError("Certificate key type does not match private key type")
                cert_numbers = cert_public_key.public_numbers()
                key_numbers = key_public_key.public_numbers()
                if cert_numbers.n != key_numbers.n or cert_numbers.e != key_numbers.e:
                    raise ValueError("Certificate and private key do not match")
            elif isinstance(private_key, ec.EllipticCurvePrivateKey):
                # ECDSA key comparison
                if not isinstance(cert_public_key, ec.EllipticCurvePublicKey):
                    raise ValueError("Certificate key type does not match private key type")
                cert_numbers = cert_public_key.public_numbers()
                key_numbers = key_public_key.public_numbers()
                if cert_numbers.x != key_numbers.x or cert_numbers.y != key_numbers.y:
                    raise ValueError("Certificate and private key do not match")
            else:
                raise ValueError(f"Unsupported key type: {type(private_key).__name__}")

            return True
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(f"Invalid certificate or key: {str(e)}") from e

    @staticmethod
    def parse_certificate_expiry(cert_content: str) -> datetime | None:
        """Parse certificate and extract expiry date.

        Args:
            cert_content: PEM-encoded certificate content (may include chain)

        Returns:
            Expiry datetime or None if parsing fails
        """
        try:
            # Extract just the first certificate from chain if present
            cert_lines = cert_content.strip().split("\n")
            cert_start = None
            cert_end = None

            for i, line in enumerate(cert_lines):
                if "-----BEGIN CERTIFICATE-----" in line:
                    cert_start = i
                elif "-----END CERTIFICATE-----" in line and cert_start is not None:
                    cert_end = i
                    break

            if cert_start is None or cert_end is None:
                return None

            # Extract just the first certificate
            first_cert_content = "\n".join(cert_lines[cert_start : cert_end + 1])

            cert = x509.load_pem_x509_certificate(first_cert_content.encode(), default_backend())
            expiry = cert.not_valid_after_utc
            return expiry.replace(tzinfo=None)  # Convert to naive UTC datetime
        except Exception as e:
            logger.error(f"Failed to parse certificate expiry: {e}")
            return None

    @staticmethod
    def save_certificate_files(
        cert_name: str, cert_content: str, key_content: str
    ) -> tuple[str, str]:
        """Save certificate and key files to disk.

        Args:
            cert_name: Certificate name (used for filename)
            cert_content: PEM-encoded certificate
            key_content: PEM-encoded private key

        Returns:
            Tuple of (cert_path, key_path)

        Raises:
            IOError: If file writing fails
        """
        os.makedirs(settings.certs_path, exist_ok=True)

        # Use sanitized cert_name for file naming
        safe_name = cert_name.replace(" ", "_").replace("/", "_")
        # Use absolute paths for Nginx compatibility
        cert_path = os.path.abspath(os.path.join(settings.certs_path, f"{safe_name}.crt"))
        key_path = os.path.abspath(os.path.join(settings.certs_path, f"{safe_name}.key"))

        with open(cert_path, "w") as f:
            f.write(cert_content)
        os.chmod(cert_path, 0o644)

        with open(key_path, "w") as f:
            f.write(key_content)
        os.chmod(key_path, 0o600)  # Restrict key permissions

        return cert_path, key_path

    @staticmethod
    def create_certificate(
        db: Session,
        name: str,
        domain: str,
        cert_content: str,
        key_content: str,
        user_id: int,
        is_default: bool = False,
    ) -> SSLCertificate:
        """Create and store a new certificate.

        Args:
            db: Database session
            name: Friendly name for certificate
            domain: Certificate domain (can be wildcard)
            cert_content: PEM-encoded certificate
            key_content: PEM-encoded private key
            user_id: ID of user uploading certificate
            is_default: Whether this is the default certificate

        Returns:
            Created certificate record

        Raises:
            ValueError: If certificate/key validation fails
        """
        # Validate certificate/key pair
        CertificateService.validate_certificate_pair(cert_content, key_content)

        # Parse expiry date
        expiry_date = CertificateService.parse_certificate_expiry(cert_content)

        # Determine certificate type
        cert_type = "wildcard" if domain.startswith("*") else "domain-specific"

        # Save files to disk
        cert_path, key_path = CertificateService.save_certificate_files(
            name, cert_content, key_content
        )

        # If setting as default, unset other defaults
        if is_default:
            db.query(SSLCertificate).filter(SSLCertificate.is_default).update({"is_default": False})

        # Create database record
        db_cert = SSLCertificate(
            name=name,
            domain=domain,
            cert_path=cert_path,
            key_path=key_path,
            certificate_type=cert_type,
            is_default=is_default,
            expiry_date=expiry_date,
            uploaded_by=user_id,
        )
        db.add(db_cert)
        db.commit()
        db.refresh(db_cert)
        return db_cert

    @staticmethod
    def get_certificate_by_domain(db: Session, domain: str) -> SSLCertificate | None:
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
    def get_expiring_certificates(db: Session, days_until_expiry: int = 30) -> list[SSLCertificate]:
        """Get certificates expiring within specified days.

        Args:
            db: Database session
            days_until_expiry: Number of days to check ahead

        Returns:
            List of expiring certificates
        """
        from sqlalchemy import and_

        cutoff_date = datetime.utcnow() + __import__("datetime").timedelta(days=days_until_expiry)

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

    @staticmethod
    def set_default_certificate(db: Session, cert_id: int) -> SSLCertificate:
        """Set a certificate as the default.

        Args:
            db: Database session
            cert_id: Certificate ID to set as default

        Returns:
            Updated certificate

        Raises:
            ValueError: If certificate not found
        """
        cert = db.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
        if not cert:
            raise ValueError(f"Certificate with ID {cert_id} not found")

        # Unset all other defaults
        db.query(SSLCertificate).filter(SSLCertificate.is_default).update({"is_default": False})

        # Set this one as default
        cert.is_default = True
        db.commit()
        db.refresh(cert)
        return cert

    @staticmethod
    def get_default_certificate(db: Session) -> SSLCertificate | None:
        """Get the default certificate.

        Args:
            db: Database session

        Returns:
            Default certificate or None
        """
        return db.query(SSLCertificate).filter(SSLCertificate.is_default).first()

    @staticmethod
    def get_certificate_for_rule(db: Session, rule: ProxyRule) -> SSLCertificate | None:
        """Get the appropriate certificate for a proxy rule.

        Resolution order:
        1. Explicit certificate_id on rule
        2. Certificate matching frontend_domain (exact or wildcard match)
        3. Default certificate

        Args:
            db: Database session
            rule: Proxy rule

        Returns:
            Certificate to use or None
        """
        # 1. Check if rule has explicit certificate
        if rule.certificate_id:
            return db.query(SSLCertificate).filter(SSLCertificate.id == rule.certificate_id).first()

        # 2. Try to find exact domain match
        exact_match = (
            db.query(SSLCertificate).filter(SSLCertificate.domain == rule.frontend_domain).first()
        )
        if exact_match:
            return exact_match

        # 3. Try wildcard match (e.g., *.example.com matches api.example.com)
        if "." in rule.frontend_domain:
            parts = rule.frontend_domain.split(".", 1)
            if len(parts) == 2:
                wildcard_domain = f"*.{parts[1]}"
                wildcard_match = (
                    db.query(SSLCertificate)
                    .filter(SSLCertificate.domain == wildcard_domain)
                    .first()
                )
                if wildcard_match:
                    return wildcard_match

        # 4. Fall back to default certificate
        return CertificateService.get_default_certificate(db)
