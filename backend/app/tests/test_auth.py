"""Tests for POST /auth/signup and POST /auth/token."""


def test_signup_success(client):
    res = client.post("/auth/signup", json={"email": "alice@example.com", "password": "Password123"})
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "alice@example.com"
    assert body["provider"] == "local"
    assert "id" in body
    assert "created_at" in body


def test_signup_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "Password123"}
    client.post("/auth/signup", json=payload)
    res = client.post("/auth/signup", json=payload)
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


def test_signup_invalid_email_format(client):
    res = client.post("/auth/signup", json={"email": "not-an-email", "password": "Password123"})
    assert res.status_code == 422


def test_signup_password_too_short(client):
    res = client.post("/auth/signup", json={"email": "user@example.com", "password": "short"})
    assert res.status_code == 422


def test_signup_missing_fields(client):
    res = client.post("/auth/signup", json={})
    assert res.status_code == 422


def test_login_success(client, registered_user):
    email, password = registered_user
    res = client.post("/auth/token", data={"username": email, "password": password})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, registered_user):
    email, _ = registered_user
    res = client.post("/auth/token", data={"username": email, "password": "WrongPassword!"})
    assert res.status_code == 401
    assert "incorrect" in res.json()["detail"].lower()


def test_login_unknown_email(client):
    res = client.post("/auth/token", data={"username": "nobody@example.com", "password": "Password123"})
    assert res.status_code == 401


def test_login_returns_bearer_token(client, registered_user):
    email, password = registered_user
    res = client.post("/auth/token", data={"username": email, "password": password})
    token = res.json()["access_token"]
    # Token should be a non-empty JWT string (three dot-separated parts)
    assert len(token.split(".")) == 3
