"""Tests for /analytics/* endpoints.

Redis is mocked globally in conftest.py (mock_redis fixture).
The agents graph is mocked via sys.modules in conftest.py.
"""
from app.agents.planner_agent import PlannerAgent
from app.agents.scheduler import Scheduler


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


# ── PlannerAgent unit tests ───────────────────────────────────────────────────

def test_planner_weak_topic_below_threshold():
    """A topic with confidence < 0.8 should appear as practice in the plan."""
    analysis = {
        "weak_topics": [{"topic": "calculus", "weakness": 0.6, "confidence": 0.4}],
        "revision_topics": [],
        "all_topics": ["calculus"],
    }
    plan = PlannerAgent().run(analysis)
    tasks = [item["task"] for item in plan]
    assert "practice" in tasks
    assert "maintain" not in tasks


def test_planner_high_confidence_single_topic_falls_back_to_maintain():
    """When only a high-confidence topic exists both lists are empty — plan should use maintain."""
    analysis = {
        "weak_topics": [],
        "revision_topics": [],
        "all_topics": ["physics"],
    }
    plan = PlannerAgent().run(analysis)
    assert len(plan) == 1
    assert plan[0]["task"] == "maintain"
    assert plan[0]["topic"] == "physics"


def test_planner_multiple_topics_mix():
    """Multiple topics: weak ones get practice, strong ones get maintain (deduped)."""
    analysis = {
        "weak_topics": [{"topic": "algebra", "weakness": 0.5, "confidence": 0.5}],
        "revision_topics": [{"topic": "calculus", "confidence": 0.7, "retention": 0.4, "revision_priority": 0.6}],
        "all_topics": ["algebra", "calculus", "geometry"],
    }
    plan = PlannerAgent().run(analysis)
    topics_in_plan = [item["topic"] for item in plan]
    # calculus should appear twice (revise + practice), algebra once (practice)
    assert topics_in_plan.count("calculus") == 2
    assert "algebra" in topics_in_plan
    # maintain tasks should NOT appear when priority tasks exist
    tasks = [item["task"] for item in plan]
    assert "maintain" not in tasks


# ── Scheduler unit tests ──────────────────────────────────────────────────────

def test_scheduler_empty_plan():
    assert Scheduler().generate_weekly_schedule([]) == []


def test_scheduler_single_maintain_topic_appears_3_times():
    """A single maintain topic should appear on days 0, 3, 6 — exactly 3 times."""
    plan = [{"topic": "physics", "task": "maintain", "priority": "low"}]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 3
    assert all(s["task"] == "maintain" for s in schedule)
    assert all(s["topic"] == "physics" for s in schedule)


def test_scheduler_multiple_maintain_topics_spread_across_3_slots():
    """Two maintain topics should each fill one of the 3 maintain slots (day 0, 3, 6)."""
    plan = [
        {"topic": "physics", "task": "maintain", "priority": "low"},
        {"topic": "chemistry", "task": "maintain", "priority": "low"},
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 3
    topics = [s["topic"] for s in schedule]
    assert "physics" in topics
    assert "chemistry" in topics


def test_scheduler_single_weak_topic_shows_3_days_revise_practice_practice():
    """Single weak topic: 3 days in order revise → practice → practice."""
    plan = [
        {"topic": "algebra", "task": "revise", "priority": "high"},
        {"topic": "algebra", "task": "practice", "priority": "medium"},
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 3
    assert [s["task"] for s in schedule] == ["revise", "practice", "practice"]


def test_scheduler_single_weak_topic_with_maintain_shows_4_days():
    """Single weak topic + one maintain topic → 3 priority days + 1 maintain day = 4 days."""
    plan = [
        {"topic": "algebra", "task": "revise", "priority": "high"},
        {"topic": "algebra", "task": "practice", "priority": "medium"},
        {"topic": "physics", "task": "maintain", "priority": "low"},
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 4
    maintain_days = [s for s in schedule if s["task"] == "maintain"]
    assert len(maintain_days) == 1
    assert maintain_days[0]["topic"] == "physics"


def test_scheduler_two_weak_topics_shows_4_days():
    """2 unique weak topics → 2×2 = 4 days, each topic gets revise then practice."""
    plan = [
        {"topic": "algebra",  "task": "revise",   "priority": "high"},
        {"topic": "algebra",  "task": "practice", "priority": "medium"},
        {"topic": "calculus", "task": "revise",   "priority": "high"},
        {"topic": "calculus", "task": "practice", "priority": "medium"},
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 4
    tasks = [s["task"] for s in schedule]
    assert tasks.count("revise") == 2
    assert tasks.count("practice") == 2


def test_scheduler_three_weak_topics_shows_6_days():
    """3 unique weak topics → 2×3 = 6 days."""
    plan = [
        {"topic": "algebra",  "task": "revise",   "priority": "high"},
        {"topic": "algebra",  "task": "practice", "priority": "medium"},
        {"topic": "calculus", "task": "revise",   "priority": "high"},
        {"topic": "calculus", "task": "practice", "priority": "medium"},
        {"topic": "geometry", "task": "revise",   "priority": "high"},
        {"topic": "geometry", "task": "practice", "priority": "medium"},
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 6


def test_scheduler_four_or_more_topics_capped_at_7():
    """4+ unique topics → capped at 7 days."""
    plan = [
        {"topic": t, "task": task, "priority": "high"}
        for t in ["algebra", "calculus", "geometry", "physics"]
        for task in ["revise", "practice"]
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    assert len(schedule) == 7


def test_scheduler_multiple_weak_topics_with_maintain():
    """2 weak topics (4 days) with 1 maintain → maintain slotted in, total 4 days."""
    plan = [
        {"topic": "algebra",  "task": "revise",   "priority": "high"},
        {"topic": "algebra",  "task": "practice", "priority": "medium"},
        {"topic": "calculus", "task": "practice", "priority": "medium"},
        {"topic": "physics",  "task": "maintain", "priority": "low"},
    ]
    schedule = Scheduler().generate_weekly_schedule(plan)
    maintain_days = [s for s in schedule if s["task"] == "maintain"]
    assert len(maintain_days) == 1
