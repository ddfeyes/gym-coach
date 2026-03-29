"""Tests for enriched /api/v1/health endpoint (issue #62)."""
import pytest


def test_health_ok_fields(client):
    resp = client.get('/api/v1/health')
    assert resp.status_code == 200
    data = resp.get_json()

    # Required fields
    assert data['status'] in ('ok', 'degraded')
    assert data['version'] == '1.0.0'
    assert data['db'] in ('ok', 'error')
    assert isinstance(data['uptime_seconds'], int)
    assert data['uptime_seconds'] >= 0
    assert isinstance(data['users_total'], int)
    assert isinstance(data['training_sessions_total'], int)
    # last_activity_at may be None when no sessions exist
    assert 'last_activity_at' in data


def test_health_db_ok(client):
    resp = client.get('/api/v1/health')
    data = resp.get_json()
    assert data['db'] == 'ok'
    assert data['status'] == 'ok'


def test_health_response_fast(client):
    """Second call should be served from cache (< 50ms)."""
    import time
    # prime cache
    client.get('/api/v1/health')
    start = time.monotonic()
    resp = client.get('/api/v1/health')
    elapsed_ms = (time.monotonic() - start) * 1000
    assert resp.status_code == 200
    assert elapsed_ms < 50, f"Response took {elapsed_ms:.1f}ms, expected < 50ms"


def test_health_counts_reflect_db(client):
    """users_total should match actual users table count."""
    from database import get_db
    db = get_db()
    count = db.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    db.close()

    # Invalidate cache
    import app as a
    with a._health_lock:
        a._health_cache["ts"] = 0

    resp = client.get('/api/v1/health')
    data = resp.get_json()
    assert data['users_total'] == count
