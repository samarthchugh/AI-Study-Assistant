"""Tests for POST /documents/upload."""
import io
from unittest.mock import patch


def test_upload_non_pdf_rejected(client, auth_headers):
    fake_file = io.BytesIO(b"plain text content")
    res = client.post(
        "/documents/upload?topic=ML",
        files={"file": ("notes.txt", fake_file, "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "pdf" in res.json()["detail"].lower()


def test_upload_unauthenticated(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
    res = client.post(
        "/documents/upload?topic=ML",
        files={"file": ("notes.pdf", fake_pdf, "application/pdf")},
    )
    assert res.status_code == 401


def test_upload_pdf_success(client, auth_headers):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    with patch("app.api.v1.documents.ingest_pdf_to_vectorstore"):
        res = client.post(
            "/documents/upload?topic=Machine+Learning",
            files={"file": ("notes.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_upload_missing_file(client, auth_headers):
    res = client.post("/documents/upload?topic=ML", headers=auth_headers)
    assert res.status_code == 422


def test_upload_missing_topic(client, auth_headers):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake")
    with patch("app.api.v1.documents.ingest_pdf_to_vectorstore"):
        res = client.post(
            "/documents/upload",
            files={"file": ("notes.pdf", fake_pdf, "application/pdf")},
            headers=auth_headers,
        )
    # topic is a required query param
    assert res.status_code == 422
