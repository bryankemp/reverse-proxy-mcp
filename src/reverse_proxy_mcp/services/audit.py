"""Audit logging service for tracking user actions."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from reverse_proxy_mcp.models.database import AuditLog, User

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging."""

    @staticmethod
    def log_action(
        db: Session,
        user: User | None,
        action: str,
        resource_type: str,
        resource_id: str,
        changes: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log a user action to the audit log.

        Args:
            db: Database session
            user: User performing the action (can be None for system actions)
            action: Action type (created, updated, deleted)
            resource_type: Type of resource (user, backend, rule, cert, config)
            resource_id: ID/identifier of the resource
            changes: Dictionary of changes (before/after values)
            ip_address: IP address of the requester

        Returns:
            Created audit log entry
        """
        changes_json = json.dumps(changes) if changes else None

        audit_log = AuditLog(
            user_id=user.id if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes_json,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        logger.info(
            f"Audit: {user.username if user else 'system'} "
            f"{action} {resource_type} {resource_id}"
        )

        return audit_log

    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: int | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get audit logs with optional filters.

        Args:
            db: Database session
            user_id: Filter by user ID
            resource_type: Filter by resource type
            action: Filter by action type
            limit: Maximum number of results

        Returns:
            List of audit log entries
        """
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if action:
            query = query.filter(AuditLog.action == action)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_user_audit_logs(db: Session, user_id: int, limit: int = 100) -> list[AuditLog]:
        """Get all audit logs for a specific user.

        Args:
            db: Database session
            user_id: User ID to filter by
            limit: Maximum number of results

        Returns:
            List of audit log entries for the user
        """
        return AuditService.get_audit_logs(db, user_id=user_id, limit=limit)

    @staticmethod
    def get_resource_audit_logs(
        db: Session, resource_type: str, resource_id: str, limit: int = 50
    ) -> list[AuditLog]:
        """Get audit logs for a specific resource.

        Args:
            db: Database session
            resource_type: Type of resource
            resource_id: ID of the resource
            limit: Maximum number of results

        Returns:
            List of audit log entries for the resource
        """
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id,
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def cleanup_old_logs(db: Session, days_retention: int = 90) -> int:
        """Delete audit logs older than the retention period.

        Args:
            db: Database session
            days_retention: Number of days to retain logs

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_retention)
        deleted_count = db.query(AuditLog).filter(AuditLog.timestamp < cutoff_date).delete()
        db.commit()

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old audit logs (>{days_retention} days)")

        return deleted_count

    @staticmethod
    def log_user_created(
        db: Session, admin_user: User, new_user: User, ip_address: str | None = None
    ) -> AuditLog:
        """Log user creation."""
        return AuditService.log_action(
            db,
            admin_user,
            "created",
            "user",
            str(new_user.id),
            {"username": new_user.username, "role": new_user.role},
            ip_address,
        )

    @staticmethod
    def log_user_updated(
        db: Session,
        admin_user: User,
        user_id: int,
        changes: dict[str, Any],
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log user update."""
        return AuditService.log_action(
            db, admin_user, "updated", "user", str(user_id), changes, ip_address
        )

    @staticmethod
    def log_user_deleted(
        db: Session, admin_user: User, user_id: int, ip_address: str | None = None
    ) -> AuditLog:
        """Log user deletion."""
        return AuditService.log_action(
            db, admin_user, "deleted", "user", str(user_id), None, ip_address
        )

    @staticmethod
    def log_backend_created(
        db: Session, user: User, backend_id: int, name: str, ip_address: str | None = None
    ) -> AuditLog:
        """Log backend server creation."""
        return AuditService.log_action(
            db,
            user,
            "created",
            "backend",
            str(backend_id),
            {"name": name},
            ip_address,
        )

    @staticmethod
    def log_rule_updated(
        db: Session,
        user: User,
        rule_id: int,
        changes: dict[str, Any],
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log proxy rule update."""
        return AuditService.log_action(
            db, user, "updated", "rule", str(rule_id), changes, ip_address
        )

    @staticmethod
    def log_config_changed(
        db: Session,
        user: User,
        changes: dict[str, Any],
        ip_address: str | None = None,
    ) -> AuditLog:
        """Log configuration change."""
        return AuditService.log_action(db, user, "updated", "config", "global", changes, ip_address)

    @staticmethod
    def log_nginx_reload(
        db: Session, user: User, success: bool, message: str, ip_address: str | None = None
    ) -> AuditLog:
        """Log Nginx reload action."""
        return AuditService.log_action(
            db,
            user,
            "executed",
            "nginx",
            "reload",
            {"success": success, "message": message},
            ip_address,
        )
