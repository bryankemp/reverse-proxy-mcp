"""Metrics service for proxy performance tracking."""

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from reverse_proxy_mcp.models.database import BackendServer, Metric


class MetricsService:
    """Service for managing proxy metrics."""

    @staticmethod
    def get_metrics(
        db: Session,
        backend_id: int | None = None,
        hours: int = 24,
        limit: int = 100,
    ) -> list[Metric]:
        """Get metrics with optional filtering.

        Args:
            db: Database session
            backend_id: Optional backend ID to filter by
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of results

        Returns:
            List of metric records
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(Metric).filter(Metric.timestamp >= cutoff_time)

        if backend_id is not None:
            query = query.filter(Metric.backend_id == backend_id)

        return query.order_by(Metric.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_summary(db: Session, hours: int = 24) -> dict:
        """Get aggregate metrics summary.

        Args:
            db: Database session
            hours: Number of hours to look back

        Returns:
            Dictionary with aggregate metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        metrics = (
            db.query(
                func.sum(Metric.request_count).label("total_requests"),
                func.avg(Metric.avg_response_time).label("avg_response_time"),
                func.avg(Metric.error_rate).label("avg_error_rate"),
                func.sum(Metric.status_2xx).label("total_2xx"),
                func.sum(Metric.status_3xx).label("total_3xx"),
                func.sum(Metric.status_4xx).label("total_4xx"),
                func.sum(Metric.status_5xx).label("total_5xx"),
            )
            .filter(Metric.timestamp >= cutoff_time)
            .first()
        )

        return {
            "total_requests": metrics.total_requests or 0,
            "avg_response_time_ms": round(metrics.avg_response_time or 0, 2),
            "avg_error_rate": round(metrics.avg_error_rate or 0, 2),
            "status_2xx": metrics.total_2xx or 0,
            "status_3xx": metrics.total_3xx or 0,
            "status_4xx": metrics.total_4xx or 0,
            "status_5xx": metrics.total_5xx or 0,
            "period_hours": hours,
        }

    @staticmethod
    def get_backend_metrics(db: Session, backend_id: int, hours: int = 24) -> dict:
        """Get metrics for a specific backend.

        Args:
            db: Database session
            backend_id: Backend ID
            hours: Number of hours to look back

        Returns:
            Dictionary with backend-specific metrics
        """
        backend = db.query(BackendServer).filter(BackendServer.id == backend_id).first()
        if not backend:
            raise ValueError(f"Backend {backend_id} not found")

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        metrics = (
            db.query(
                func.sum(Metric.request_count).label("total_requests"),
                func.avg(Metric.avg_response_time).label("avg_response_time"),
                func.avg(Metric.error_rate).label("error_rate"),
            )
            .filter(
                Metric.backend_id == backend_id,
                Metric.timestamp >= cutoff_time,
            )
            .first()
        )

        return {
            "backend_id": backend_id,
            "backend_name": backend.name,
            "total_requests": metrics.total_requests or 0,
            "avg_response_time_ms": round(metrics.avg_response_time or 0, 2),
            "error_rate": round(metrics.error_rate or 0, 2),
            "period_hours": hours,
        }

    @staticmethod
    def record_request(
        db: Session,
        backend_id: int | None,
        response_time_ms: float,
        status_code: int,
    ) -> None:
        """Record a single request for metrics tracking.

        Args:
            db: Database session
            backend_id: Backend ID (None for aggregate)
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
        """
        # Get or create metric record for current hour
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        metric = (
            db.query(Metric)
            .filter(
                Metric.timestamp == current_hour,
                Metric.backend_id == backend_id,
            )
            .first()
        )

        if not metric:
            metric = Metric(timestamp=current_hour, backend_id=backend_id)
            db.add(metric)

        # Update counters
        metric.request_count += 1

        # Update average response time (running average)
        if metric.avg_response_time is None:
            metric.avg_response_time = response_time_ms
        else:
            total_time = metric.avg_response_time * (metric.request_count - 1)
            metric.avg_response_time = (total_time + response_time_ms) / metric.request_count

        # Update status code counters
        if 200 <= status_code < 300:
            metric.status_2xx += 1
        elif 300 <= status_code < 400:
            metric.status_3xx += 1
        elif 400 <= status_code < 500:
            metric.status_4xx += 1
        elif 500 <= status_code < 600:
            metric.status_5xx += 1

        # Calculate error rate
        total_errors = metric.status_4xx + metric.status_5xx
        metric.error_rate = (
            (total_errors / metric.request_count) * 100 if metric.request_count > 0 else 0
        )

        db.commit()

    @staticmethod
    def cleanup_old_metrics(db: Session, days_retention: int = 30) -> int:
        """Delete metrics older than retention period.

        Args:
            db: Database session
            days_retention: Number of days to keep (default: 30)

        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_retention)
        deleted_count = db.query(Metric).filter(Metric.timestamp < cutoff_date).delete()
        db.commit()
        return deleted_count
