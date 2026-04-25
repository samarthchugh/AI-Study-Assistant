"""Tests for POST /rag/ask and POST /rag/ask-stream."""
from unittest.mock import patch


_MOCK_ANSWER = {
    "answer": "Deep learning is a subset of machine learning using neural networks.",
    "sources": ["lecture_notes.pdf"],
    "confidence": 0.92,
}


# ── Auth guards ───────────────────────────────────────────────────────────────

def test_ask_unauthenticated(client):
    res = client.post("/rag/ask", json={"question": "What is deep learning?"})
    assert res.status_code == 401


def test_ask_stream_unauthenticated(client):
    res = client.post("/rag/ask-stream", json={"question": "What is deep learning?"})
    assert res.status_code == 401


# ── Authenticated ─────────────────────────────────────────────────────────────

def test_ask_success(client, auth_headers):
    with patch("app.api.v1.rag.pipeline") as mock_pipeline:
        mock_pipeline.answer_query.return_value = _MOCK_ANSWER
        res = client.post(
            "/rag/ask",
            json={"question": "What is deep learning?"},
            headers=auth_headers,
        )

    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == _MOCK_ANSWER["answer"]
    assert data["sources"] == _MOCK_ANSWER["sources"]
    assert data["confidence"] == _MOCK_ANSWER["confidence"]


def test_ask_empty_question_rejected(client, auth_headers):
    res = client.post("/rag/ask", json={"question": ""}, headers=auth_headers)
    assert res.status_code == 422


def test_ask_missing_question_rejected(client, auth_headers):
    res = client.post("/rag/ask", json={}, headers=auth_headers)
    assert res.status_code == 422


def test_ask_pipeline_error_returns_500(client, auth_headers):
    with patch("app.api.v1.rag.pipeline") as mock_pipeline:
        mock_pipeline.answer_query.side_effect = RuntimeError("FAISS index not loaded")
        res = client.post(
            "/rag/ask",
            json={"question": "What is ML?"},
            headers=auth_headers,
        )
    assert res.status_code == 500
