"""Tests for quiz CRUD: generate, list, get, start, submit."""
from unittest.mock import MagicMock, patch


# ── Generate ──────────────────────────────────────────────────────────────────

def test_generate_quiz_unauthenticated(client):
    res = client.post("/quiz/generate?topic=ML")
    assert res.status_code == 401


def test_generate_quiz_success(client, auth_headers):
    mock_quiz = MagicMock()
    mock_quiz.id = 1
    mock_quiz.topic = "machine learning"
    mock_quiz.difficulty_level = 2
    mock_quiz.total_questions = 5

    with patch("app.api.v1.quiz.QuizEngine") as MockEngine:
        MockEngine.return_value.generate_quiz.return_value = mock_quiz
        res = client.post(
            "/quiz/generate?topic=machine+learning&num_questions=5",
            headers=auth_headers,
        )

    assert res.status_code == 200
    data = res.json()
    assert data["topic"] == "machine learning"
    assert data["total_questions"] == 5
    assert "quiz_id" in data
    assert "difficulty" in data


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_quizzes_unauthenticated(client):
    res = client.get("/quiz/my-quizzes")
    assert res.status_code == 401


def test_list_quizzes_empty(client, auth_headers):
    res = client.get("/quiz/my-quizzes", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["quizzes"] == []


def test_list_quizzes_returns_quiz(client, auth_headers, sample_quiz):
    res = client.get("/quiz/my-quizzes", headers=auth_headers)
    assert res.status_code == 200
    quizzes = res.json()["quizzes"]
    assert len(quizzes) == 1
    assert quizzes[0]["topic"] == "machine learning"
    assert quizzes[0]["status"] == "not_started"
    assert quizzes[0]["quiz_id"] == sample_quiz["id"]


# ── Get ───────────────────────────────────────────────────────────────────────

def test_get_quiz_unauthenticated(client, sample_quiz):
    res = client.get(f"/quiz/{sample_quiz['id']}")
    assert res.status_code == 401


def test_get_quiz_success(client, auth_headers, sample_quiz):
    res = client.get(f"/quiz/{sample_quiz['id']}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["quiz_id"] == sample_quiz["id"]
    assert data["topic"] == "machine learning"
    assert len(data["questions"]) == 2


def test_get_quiz_questions_have_required_fields(client, auth_headers, sample_quiz):
    res = client.get(f"/quiz/{sample_quiz['id']}", headers=auth_headers)
    q = res.json()["questions"][0]
    assert "question_id" in q
    assert "question_text" in q
    assert "options" in q


# ── Start ─────────────────────────────────────────────────────────────────────

def test_start_quiz_unauthenticated(client, sample_quiz):
    res = client.post(f"/quiz/{sample_quiz['id']}/start")
    assert res.status_code == 401


def test_start_quiz_success(client, auth_headers, sample_quiz):
    res = client.post(f"/quiz/{sample_quiz['id']}/start", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "attempt_id" in data
    assert "start_time" in data
    assert data["message"] == "Quiz started"


def test_start_quiz_not_found(client, auth_headers):
    res = client.post("/quiz/99999/start", headers=auth_headers)
    assert res.status_code == 400


# ── Submit ────────────────────────────────────────────────────────────────────

def test_submit_quiz_unauthenticated(client, sample_quiz):
    res = client.post(
        f"/quiz/{sample_quiz['id']}/submit?attempt_id=1",
        json={"answers": []},
    )
    assert res.status_code == 401


def test_submit_quiz_success(client, auth_headers, sample_quiz):
    # Start quiz first to get attempt_id
    start_res = client.post(f"/quiz/{sample_quiz['id']}/start", headers=auth_headers)
    assert start_res.status_code == 200
    attempt_id = start_res.json()["attempt_id"]
    q_ids = sample_quiz["question_ids"]

    answers = [
        {"question_id": q_ids[0], "answer": "A"},           # MCQ correct answer
        {"question_id": q_ids[1], "answer": "model memorizes training data"},  # short partial match
    ]
    res = client.post(
        f"/quiz/{sample_quiz['id']}/submit?attempt_id={attempt_id}",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["quiz_id"] == sample_quiz["id"]
    assert data["total_questions"] == 2
    assert 0.0 <= data["score_ratio"] <= 1.0
    assert "new_difficulty" in data
    assert "updated_mastery" in data


def test_submit_quiz_wrong_answer_count(client, auth_headers, sample_quiz):
    start_res = client.post(f"/quiz/{sample_quiz['id']}/start", headers=auth_headers)
    attempt_id = start_res.json()["attempt_id"]

    # Send only 1 answer instead of 2
    answers = [{"question_id": sample_quiz["question_ids"][0], "answer": "A"}]
    res = client.post(
        f"/quiz/{sample_quiz['id']}/submit?attempt_id={attempt_id}",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert res.status_code == 500  # ValueError raised inside endpoint


def test_submit_quiz_correct_score(client, auth_headers, sample_quiz):
    """Both answers fully correct → score_ratio == 1.0."""
    start_res = client.post(f"/quiz/{sample_quiz['id']}/start", headers=auth_headers)
    attempt_id = start_res.json()["attempt_id"]
    q_ids = sample_quiz["question_ids"]

    answers = [
        {"question_id": q_ids[0], "answer": "A"},
        {"question_id": q_ids[1], "answer": "model memorizes training data and fails to generalize"},
    ]
    res = client.post(
        f"/quiz/{sample_quiz['id']}/submit?attempt_id={attempt_id}",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["score_ratio"] == 1.0
    assert res.json()["correct_answers"] == 2
