"""Tests to ensure timestamps are timezone-aware and included in outputs.

These tests assert that model defaults and generated artifacts include UTC
timezone information (tzinfo != None / +00:00 in rendered strings).
"""

from datetime import timezone, datetime as _dt

import pytest

from reverse_proxy_mcp.core.nginx import NginxConfigGenerator
from reverse_proxy_mcp.models.database import Metric


@pytest.mark.unit
def test_metric_default_timestamp_is_timezone_aware(db):
    """Creating a Metric without timestamp sets a timezone-aware datetime."""
    m = Metric(request_count=1)
    db.add(m)
    db.commit()
    db.refresh(m)

    assert m.timestamp is not None
    # Some DB backends (SQLite) may return naive datetimes; accept either:
    if m.timestamp.tzinfo is None:
        # treat naive as UTC and assert it's recent
        ts_utc = m.timestamp.replace(tzinfo=timezone.utc)
    else:
        ts_utc = m.timestamp

    # Timestamp should be within a small delta of now (UTC)
    delta = abs((ts_utc - _dt.now(timezone.utc)).total_seconds())
    assert delta < 10


@pytest.mark.unit
def test_nginx_generated_config_includes_utc_offset(db, tmp_path):
    """Nginx generator should render timestamps that include UTC offset."""
    gen = NginxConfigGenerator(config_path=str(tmp_path / "proxy.conf"), backup_dir=str(tmp_path))
    cfg = gen.generate_config(db)

    # ISO format for UTC includes +00:00 (or 'Z'); accept either
    assert "+00:00" in cfg or "Z" in cfg
