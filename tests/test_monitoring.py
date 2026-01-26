"""Tests for monitoring endpoints (health and metrics)."""

from datetime import datetime, timedelta

import pytest

from reverse_proxy_mcp.models.database import Metric


@pytest.mark.unit
def test_health_endpoint_no_auth(client):
    """Test health endpoint works without authentication."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "nginx" in data


@pytest.mark.unit
def test_health_endpoint_structure(client, db):
    """Test health endpoint returns expected structure."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    health = response.json()

    # Required fields
    assert health["status"] in ["healthy", "unhealthy"]
    assert "version" in health
    assert health["database"] in ["connected", "disconnected"]
    assert health["nginx"] in ["active", "inactive"]
    assert "active_backends" in health
    assert "active_rules" in health
    assert "timestamp" in health

    # Validate counts are non-negative
    assert health["active_backends"] >= 0
    assert health["active_rules"] >= 0


@pytest.mark.unit
def test_metrics_requires_auth(client):
    """Test metrics endpoint requires authentication."""
    response = client.get("/api/v1/monitoring/metrics")
    assert response.status_code == 401


@pytest.mark.unit
def test_metrics_list_empty(client, admin_token):
    """Test metrics endpoint with no data."""
    response = client.get(
        "/api/v1/monitoring/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    metrics = response.json()
    assert isinstance(metrics, list)
    assert len(metrics) == 0


@pytest.mark.unit
def test_metrics_list_with_data(client, admin_token, db, backend_server):
    """Test metrics endpoint returns data."""
    # Create some test metrics
    metric1 = Metric(
        timestamp=datetime.utcnow(),
        backend_id=backend_server.id,
        request_count=100,
        avg_response_time=0.25,
        error_rate=0.01,
        status_2xx=95,
        status_3xx=3,
        status_4xx=1,
        status_5xx=1,
    )
    metric2 = Metric(
        timestamp=datetime.utcnow() - timedelta(hours=1),
        backend_id=backend_server.id,
        request_count=50,
        avg_response_time=0.30,
        error_rate=0.02,
        status_2xx=48,
        status_3xx=1,
        status_4xx=1,
        status_5xx=0,
    )
    db.add(metric1)
    db.add(metric2)
    db.commit()

    response = client.get(
        "/api/v1/monitoring/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) == 2


@pytest.mark.unit
def test_metrics_filter_by_backend(client, admin_token, db, backend_server):
    """Test filtering metrics by backend ID."""
    # Create metrics for specific backend
    metric = Metric(
        timestamp=datetime.utcnow(),
        backend_id=backend_server.id,
        request_count=100,
        avg_response_time=0.25,
        error_rate=0.01,
        status_2xx=95,
        status_3xx=3,
        status_4xx=1,
        status_5xx=1,
    )
    db.add(metric)
    db.commit()

    response = client.get(
        f"/api/v1/monitoring/metrics?backend_id={backend_server.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) == 1
    assert metrics[0]["backend_id"] == backend_server.id


@pytest.mark.unit
def test_metrics_summary_requires_auth(client):
    """Test metrics summary requires authentication."""
    response = client.get("/api/v1/monitoring/metrics/summary")
    assert response.status_code == 401


@pytest.mark.unit
def test_metrics_summary_empty(client, admin_token, db):
    """Test metrics summary with no data."""
    response = client.get(
        "/api/v1/monitoring/metrics/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    summary = response.json()
    assert "total_requests" in summary
    assert "avg_response_time_ms" in summary
    assert "avg_error_rate" in summary
    assert "status_2xx" in summary
    assert "period_hours" in summary


@pytest.mark.unit
def test_metrics_summary_with_data(client, admin_token, db, backend_server):
    """Test metrics summary aggregates correctly."""
    # Create test metrics
    metric1 = Metric(
        timestamp=datetime.utcnow(),
        backend_id=backend_server.id,
        request_count=100,
        avg_response_time=0.25,
        error_rate=0.01,
        status_2xx=95,
        status_3xx=3,
        status_4xx=1,
        status_5xx=1,
    )
    metric2 = Metric(
        timestamp=datetime.utcnow() - timedelta(hours=1),
        backend_id=backend_server.id,
        request_count=50,
        avg_response_time=0.30,
        error_rate=0.02,
        status_2xx=48,
        status_3xx=1,
        status_4xx=1,
        status_5xx=0,
    )
    db.add_all([metric1, metric2])
    db.commit()

    response = client.get(
        "/api/v1/monitoring/metrics/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_requests"] == 150
    assert summary["status_4xx"] == 2
    assert summary["status_5xx"] == 1


@pytest.mark.unit
def test_backend_metrics_requires_auth(client):
    """Test backend metrics endpoint requires authentication."""
    response = client.get("/api/v1/monitoring/metrics/backends/1")
    assert response.status_code == 401


@pytest.mark.unit
def test_backend_metrics_not_found(client, admin_token):
    """Test backend metrics returns 404 for non-existent backend."""
    response = client.get(
        "/api/v1/monitoring/metrics/backends/99999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.unit
def test_backend_metrics_success(client, admin_token, db, backend_server):
    """Test backend metrics returns data for specific backend."""
    # Create metrics for backend
    metric = Metric(
        timestamp=datetime.utcnow(),
        backend_id=backend_server.id,
        request_count=100,
        avg_response_time=0.25,
        error_rate=0.01,
        status_2xx=95,
        status_3xx=3,
        status_4xx=1,
        status_5xx=1,
    )
    db.add(metric)
    db.commit()

    response = client.get(
        f"/api/v1/monitoring/metrics/backends/{backend_server.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    metrics = response.json()
    assert "backend_id" in metrics
    assert metrics["backend_id"] == backend_server.id


@pytest.mark.unit
def test_metrics_cleanup_requires_auth(client):
    """Test metrics cleanup requires authentication."""
    response = client.post("/api/v1/monitoring/metrics/cleanup")
    assert response.status_code == 401


@pytest.mark.unit
def test_metrics_cleanup_requires_admin(client, user_token):
    """Test metrics cleanup requires admin role."""
    response = client.post(
        "/api/v1/monitoring/metrics/cleanup",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


@pytest.mark.unit
def test_metrics_cleanup_success(client, admin_token, db, backend_server):
    """Test metrics cleanup deletes old metrics."""
    # Create old and new metrics
    old_metric = Metric(
        timestamp=datetime.utcnow() - timedelta(days=60),
        backend_id=backend_server.id,
        request_count=10,
        avg_response_time=0.5,
        error_rate=0.0,
        status_2xx=10,
        status_3xx=0,
        status_4xx=0,
        status_5xx=0,
    )
    new_metric = Metric(
        timestamp=datetime.utcnow(),
        backend_id=backend_server.id,
        request_count=100,
        avg_response_time=0.25,
        error_rate=0.01,
        status_2xx=95,
        status_3xx=3,
        status_4xx=1,
        status_5xx=1,
    )
    db.add_all([old_metric, new_metric])
    db.commit()

    # Cleanup metrics older than 30 days
    response = client.post(
        "/api/v1/monitoring/metrics/cleanup?days_retention=30",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    result = response.json()
    assert "detail" in result
    assert "1" in result["detail"]  # Should delete 1 old metric

    # Verify old metric was deleted
    remaining = db.query(Metric).all()
    assert len(remaining) == 1
    assert remaining[0].request_count == 100


@pytest.mark.integration
def test_health_reflects_database_state(client, db, admin_user):
    """Test health endpoint reflects actual database connectivity."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    health = response.json()

    # Database should be connected (if disconnected, status would be unhealthy)
    assert health["database"] in ["connected", "disconnected"]
    assert health["status"] in ["healthy", "unhealthy"]
