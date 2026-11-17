from freezegun import freeze_time

from tests.conftest import auth_header


@freeze_time("2027-03-10 10:00:00")
async def test_player_creates_booking(client, player_user, court):
    headers = await auth_header(client, "player1", "player123")
    resp = await client.post(
        "/bookings/",
        json={
            "court_id": court.id,
            "booking_type": "private",
            "starts_at": "2027-03-15T18:00:00+01:00",
            "ends_at": "2027-03-15T19:30:00+01:00",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["phase"] == "open_change"


@freeze_time("2027-03-10 10:00:00")
async def test_player_cannot_view_other_player_booking(
    client, player_user, other_player_user, court
):
    h1 = await auth_header(client, "player1", "player123")
    h2 = await auth_header(client, "player2", "player123")
    created = await client.post(
        "/bookings/",
        json={
            "court_id": court.id,
            "booking_type": "private",
            "starts_at": "2027-03-15T18:00:00+01:00",
            "ends_at": "2027-03-15T19:30:00+01:00",
        },
        headers=h1,
    )
    booking_id = created.json()["id"]

    resp = await client.get(f"/bookings/{booking_id}", headers=h2)
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


@freeze_time("2027-03-10 10:00:00")
async def test_overlapping_booking_is_409(
    client, player_user, other_player_user, court
):
    h1 = await auth_header(client, "player1", "player123")
    h2 = await auth_header(client, "player2", "player123")
    payload = {
        "court_id": court.id,
        "booking_type": "private",
        "starts_at": "2027-03-15T18:00:00+01:00",
        "ends_at": "2027-03-15T19:30:00+01:00",
    }
    await client.post("/bookings/", json=payload, headers=h1)

    resp = await client.post("/bookings/", json=payload, headers=h2)
    assert resp.status_code == 409
    assert resp.json()["code"] == "slot_conflict"
