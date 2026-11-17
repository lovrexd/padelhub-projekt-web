from tests.conftest import auth_header

NEW_COURT = {
    "name": "Teren 2",
    "surface": "outdoor",
    "hourly_rate": 27,
}


async def test_player_lists_courts(client, player_user, court):
    headers = await auth_header(client, "player1", "player123")
    resp = await client.get("/courts/", headers=headers)
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json()] == ["Teren 1"]


async def test_admin_creates_court(client, admin_user):
    headers = await auth_header(client, "testadmin", "admin123")
    resp = await client.post("/courts/", json=NEW_COURT, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Teren 2"


async def test_player_cannot_create_court(client, player_user):
    headers = await auth_header(client, "player1", "player123")
    resp = await client.post("/courts/", json=NEW_COURT, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"
