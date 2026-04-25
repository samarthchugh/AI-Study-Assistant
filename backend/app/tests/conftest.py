"""
Pytest configuration and shared fixtures.

Run from backend/ with:  pytest
Requires a PostgreSQL database named test_study_db (override via TEST_DATABASE_URL).
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Patch module-level singletons BEFORE app is imported ────────────────────
# vector_store_instance calls embed_text() at module load — replace entirely.
_vs_module = MagicMock()
_vs_module.vector_store = MagicMock()
sys.modules["app.services.vector_store_instance"] = _vs_module

# agents.graph imports LangGraph + heavy LLM chains — replace entirely.
_mock_graph = MagicMock()
_mock_graph.invoke.return_value = {"schedule": []}
_graph_module = MagicMock()
_graph_module.app_graph = _mock_graph
sys.modules["app.agents.graph"] = _graph_module

# ── App imports (after sys.modules patches) ──────────────────────────────────
from app.main import app  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.db.models import Base  # noqa: E402

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:Cypher001@localhost:5432/test_study_db",
)

engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSession = sessionmaker(bind=engine, autoflush=False)

# All modules that import redis_client at module level
_REDIS_MODULES = [
    "app.api.v1.analytics.redis_client",
    "app.api.v1.documents.redis_client",
    "app.services.intelligence_service.redis_client",
    "app.services.quiz_engine.redis_client",
]


# ── DB lifecycle ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables():
    """Delete all rows before each test so every test starts with a clean DB."""
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


# ── Redis mock ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.smembers.return_value = set()
    r.zrevrange.return_value = []
    r.lrange.return_value = []
    r.get.return_value = None
    return r


# ── HTTP client ───────────────────────────────────────────────────────────────

@pytest.fixture
def client(mock_redis):
    def _override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db

    active_patches = [patch(target, mock_redis) for target in _REDIS_MODULES]
    for p in active_patches:
        p.start()

    with TestClient(app) as c:
        yield c

    for p in active_patches:
        p.stop()
    app.dependency_overrides.pop(get_db, None)


# ── Auth helpers ─────────────────────────────────────────────────────────────

@pytest.fixture
def registered_user(client):
    """Create a unique test user, return (email, password)."""
    email = f"user_{os.urandom(4).hex()}@test.com"
    password = "TestPass123"
    res = client.post("/auth/signup", json={"email": email, "password": password})
    assert res.status_code == 200
    return email, password


@pytest.fixture
def auth_headers(client, registered_user):
    email, password = registered_user
    res = client.post("/auth/token", data={"username": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def user_id(client, auth_headers):
    res = client.get("/users/me", headers=auth_headers)
    assert res.status_code == 200
    return int(res.json()["user_id"])


# ── Quiz fixture ──────────────────────────────────────────────────────────────

@pytest.fixture
def sample_quiz(user_id):
    """
    Insert a quiz with 2 questions directly in the test DB.
    Returns a plain dict (not an ORM object) to avoid DetachedInstanceError.
    """
    from datetime import datetime, timezone
    from app.db.models import Quiz, Question

    db = TestingSession()
    try:
        quiz = Quiz(
            user_id=user_id,
            topic="machine learning",
            difficulty_level=2,
            total_questions=2,
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        db.add(quiz)
        db.flush()

        q1 = Question(
            quiz_id=quiz.id,
            question_text="What is supervised learning?",
            question_type="mcq",
            options={
                "A": "Learning with labels",
                "B": "Learning without labels",
                "C": "Reinforcement",
                "D": "Deep learning",
            },
            correct_answer="A",
            difficulty_level=2,
        )
        q2 = Question(
            quiz_id=quiz.id,
            question_text="Define overfitting",
            question_type="short",
            options=None,
            correct_answer="model memorizes training data and fails to generalize",
            difficulty_level=2,
        )
        db.add_all([q1, q2])
        db.commit()

        return {
            "id": quiz.id,
            "topic": quiz.topic,
            "difficulty_level": quiz.difficulty_level,
            "total_questions": quiz.total_questions,
            "question_ids": [q1.id, q2.id],
        }
    finally:
        db.close()
