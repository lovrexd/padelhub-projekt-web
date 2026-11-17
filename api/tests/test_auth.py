from tests.conftest import auth_header


async def login(client, username, password):
    return await client.post(
        "/auth/login", json={"username": username, "password": password}
    )


async def test_login_success_returns_both_tokens(client, admin_user):
    resp = await login(client, "testadmin", "admin123")
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


async def test_login_failure(client):
    resp = await login(client, "nonexistent", "wrongpassword")
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_auth_me(client, player_user):
    header = await auth_header(client, "player1", "player123")
    resp = await client.get("/auth/me", headers=header)
    assert resp.status_code == 200
    assert resp.json()["username"] == "player1"
    assert "password_hash" not in resp.json()


async def test_auth_me_unauthorized(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"
