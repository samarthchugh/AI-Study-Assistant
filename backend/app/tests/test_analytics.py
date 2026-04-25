"""Tests for /analytics/* endpoints.

Redis is mocked globally in conftest.py (mock_redis fixture).
The agents graph is mocked via sys.modules in conftest.py.
"""


# ── Auth guards ───────────────────────────────────────────────────────────────

def test_overview_unauthenticated(client):
    assert client.get("/analytics/overview").status_code == 401


def test_weak_topics_unauthenticated(client):
    assert client.get("/analytics/weak-topics").status_code == 401


def test_all_topics_unauthenticated(client):
    assert client.get("/analytics/all-topics").status_code == 401


def test_confidence_unauthenticated(client):
    assert client.get("/analytics/confidence?topic=ml").status_code == 401


def test_revision_unauthenticated(client):
    assert client.get("/analytics/revision").status_code == 401


def test_recommend_smart_unauthenticated(client):
    assert client.get("/analytics/recommend-smart").status_code == 401


def test_weekly_plan_unauthenticated(client):
    assert client.get("/analytics/weekly-plan").status_code == 401


# ── Authenticated: empty Redis state ─────────────────────────────────────────

def test_overview_empty(client, auth_headers):
    res = client.get("/analytics/overview", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data
    assert data["topics"] == []
    assert data["weak_topics"] == []
    assert data["confidence_map"] == {}


def test_weak_topics_empty(client, auth_headers):
    res = client.get("/analytics/weak-topics", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data
    assert data["weak_topics"] == []


def test_all_topics_empty(client, auth_headers):
    res = client.get("/analytics/all-topics", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data
    assert data["topics"] == []


def test_confidence_returns_zero_for_unknown_topic(client, auth_headers):
    res = client.get("/analytics/confidence?topic=unknown_topic", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["confidence"] == 0.0
    assert "topic" in data


def test_revision_empty(client, auth_headers):
    res = client.get("/analytics/revision", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data
    assert data["revision_topics"] == []


def test_recommend_smart_no_topics(client, auth_headers):
    """With no topics in Redis the endpoint should return a no_content status."""
    res = client.get("/analytics/recommend-smart", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "no_content" or data.get("recommended_topic") is None


def test_weekly_plan_returns_schedule(client, auth_headers):
    """agents.graph is mocked to return an empty schedule list."""
    res = client.get("/analytics/weekly-plan", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "weekly_plan" in data
    assert isinstance(data["weekly_plan"], list)
    assert "user_id" in data


# ── recommend_smart with populated Redis ─────────────────────────────────────

def test_recommend_smart_with_topics(client, auth_headers, mock_redis):
    """When Redis has a topic, recommend-smart should return a recommendation."""
    mock_redis.smembers.return_value = {"machine learning"}
    mock_redis.get.return_value = "0.6"  # confidence value
    mock_redis.lrange.return_value = []  # no attempt history

    res = client.get("/analytics/recommend-smart", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get("recommended_topic") == "machine learning"
    assert "reason" in data
