"""Tests for GET /users/me."""


def test_me_returns_user_id(client, auth_headers):
    res = client.get("/users/me", headers=auth_headers)
    assert res.status_code == 200
    assert "user_id" in res.json()


def test_me_user_id_is_integer(client, auth_headers):
    res = client.get("/users/me", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(int(res.json()["user_id"]), int)


def test_me_no_token(client):
    res = client.get("/users/me")
    assert res.status_code == 401


def test_me_invalid_token(client):
    res = client.get("/users/me", headers={"Authorization": "Bearer this.is.invalid"})
    assert res.status_code == 401


def test_me_malformed_header(client):
    res = client.get("/users/me", headers={"Authorization": "NotBearer sometoken"})
    assert res.status_code == 401
