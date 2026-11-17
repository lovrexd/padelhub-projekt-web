from datetime import datetime, timedelta, timezone

from freezegun import freeze_time

from app.models import Court
from tests.conftest import auth_header


def _slot_payload(court_id: int, booking_type: str = "private", hour: int = 18):
    start = datetime(2026, 12, 10, hour, 0, tzinfo=timezone.utc)
    return {
        "court_id": court_id,
        "booking_type": booking_type,
        "starts_at": start.isoformat(),
        "ends_at": (start + timedelta(minutes=90)).isoformat(),
    }


@freeze_time("2026-12-08 10:00:00+00:00")
async def test_create_booking_and_prevent_overlap(
    client, player_user, other_player_user, court
):
    h1 = await auth_header(client, "player1", "player123")
    h2 = await auth_header(client, "player2", "player123")

    r1 = await client.post("/bookings/", json=_slot_payload(court.id), headers=h1)
    assert r1.status_code == 201
    data = r1.json()
    assert data["phase"] == "open_change"
    assert data["active_players_count"] == 0

    # Termin koji počinje usred postojeće rezervacije (18:30 - 20:00) mora pasti s 409
    overlap_start = datetime(2026, 12, 10, 18, 30, tzinfo=timezone.utc)
    r2 = await client.post(
        "/bookings/",
        json={
            "court_id": court.id,
            "booking_type": "private",
            "starts_at": overlap_start.isoformat(),
            "ends_at": (overlap_start + timedelta(minutes=90)).isoformat(),
        },
        headers=h2,
    )
    assert r2.status_code == 409
    assert r2.json()["code"] == "slot_conflict"


@freeze_time("2026-12-08 10:00:00+00:00")
async def test_open_match_starts_with_creator_as_first_participant(
    client, player_user, court
):
    headers = await auth_header(client, "player1", "player123")
    resp = await client.post(
        "/bookings/",
        json=_slot_payload(court.id, booking_type="open_match"),
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["active_players_count"] == 1


@freeze_time("2026-12-08 10:00:00+00:00")
async def test_ownership_player_cannot_see_or_modify_other_player_booking(
    client, admin_user, player_user, other_player_user, court
):
    h1 = await auth_header(client, "player1", "player123")
    h2 = await auth_header(client, "player2", "player123")
    h_admin = await auth_header(client, "testadmin", "admin123")

    b1 = (
        await client.post(
            "/bookings/", json=_slot_payload(court.id, hour=14), headers=h1
        )
    ).json()
    await client.post("/bookings/", json=_slot_payload(court.id, hour=16), headers=h2)

    # Popis za player1 vraća isključivo njegove rezervacije
    list_p1 = await client.get("/bookings/", headers=h1)
    assert list_p1.status_code == 200
    assert [b["id"] for b in list_p1.json()] == [b1["id"]]

    # Admin vidi obje rezervacije
    list_admin = await client.get("/bookings/", headers=h_admin)
    assert len(list_admin.json()) == 2

    # player2 ne može vidjeti, mijenjati ni otkazati rezervaciju player1 (IDOR -> 403)
    assert (await client.get(f"/bookings/{b1['id']}", headers=h2)).status_code == 403
    assert (
        await client.patch(
            f"/bookings/{b1['id']}",
            json={"max_players": 2},
            headers=h2,
        )
    ).status_code == 403
    assert (
        await client.post(f"/bookings/{b1['id']}/cancel", headers=h2)
    ).status_code == 403


@freeze_time("2026-12-08 10:00:00+00:00")
async def test_cannot_book_past_slot_or_inactive_court(client, db, player_user):
    headers = await auth_header(client, "player1", "player123")
    inactive = Court(
        name="Ugašen teren", surface="outdoor", hourly_rate=20, is_active=False
    )
    db.add(inactive)
    await db.commit()

    past_start = datetime(2026, 12, 8, 9, 0, tzinfo=timezone.utc)
    r_past = await client.post(
        "/bookings/",
        json={
            "court_id": inactive.id,
            "booking_type": "private",
            "starts_at": past_start.isoformat(),
            "ends_at": (past_start + timedelta(minutes=60)).isoformat(),
        },
        headers=headers,
    )
    assert r_past.status_code == 400
    assert r_past.json()["code"] == "slot_in_past"

    r_inactive = await client.post(
        "/bookings/", json=_slot_payload(inactive.id), headers=headers
    )
    assert r_inactive.status_code == 400
    assert r_inactive.json()["code"] == "court_inactive"


async def test_cancel_and_reactivate_booking_with_deadline_and_conflict(
    client, player_user, other_player_user, court
):
    with freeze_time("2026-12-08 10:00:00+00:00"):
        h1 = await auth_header(client, "player1", "player123")
        h2 = await auth_header(client, "player2", "player123")

        b1 = (
            await client.post("/bookings/", json=_slot_payload(court.id), headers=h1)
        ).json()
        cancel_resp = await client.post(f"/bookings/{b1['id']}/cancel", headers=h1)
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        # Duplo otkazivanje nije dopušteno
        again = await client.post(f"/bookings/{b1['id']}/cancel", headers=h1)
        assert again.status_code == 400
        assert again.json()["code"] == "already_cancelled"

        # Dok je termin slobodan, reaktivacija prolazi
        react = await client.post(f"/bookings/{b1['id']}/reactivate", headers=h1)
        assert react.status_code == 200
        assert react.json()["status"] == "active"

        # Ponovno otkaži, pa player2 zauzme taj isti termin -> reaktivacija dobiva 409
        await client.post(f"/bookings/{b1['id']}/cancel", headers=h1)
        r_p2 = await client.post("/bookings/", json=_slot_payload(court.id), headers=h2)
        assert r_p2.status_code == 201
        react_conflict = await client.post(
            f"/bookings/{b1['id']}/reactivate", headers=h1
        )
        assert react_conflict.status_code == 409
        assert react_conflict.json()["code"] == "slot_conflict"

    # Nakon roka za otkazivanje (18:00 dan prije) nema više otkazivanja ni PATCH-a
    with freeze_time("2026-12-09 18:00:00+00:00"):
        h2_late = await auth_header(client, "player2", "player123")
        late_patch = await client.patch(
            f"/bookings/{r_p2.json()['id']}",
            json={"max_players": 2},
            headers=h2_late,
        )
        assert late_patch.status_code == 400
        assert late_patch.json()["code"] == "deadline_passed"

        late_cancel = await client.post(
            f"/bookings/{r_p2.json()['id']}/cancel", headers=h2_late
        )
        assert late_cancel.status_code == 400
        assert late_cancel.json()["code"] == "deadline_passed"


@freeze_time("2026-12-08 10:00:00+00:00")
async def test_patch_booking_updates_fields_and_rejects_null(
    client, player_user, court
):
    headers = await auth_header(client, "player1", "player123")
    b = (
        await client.post("/bookings/", json=_slot_payload(court.id), headers=headers)
    ).json()

    # PATCH dira samo max_players i min_level
    resp = await client.patch(
        f"/bookings/{b['id']}",
        json={"max_players": 2, "min_level": 3.0},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["max_players"] == 2
    assert resp.json()["min_level"] == 3.0
    assert resp.json()["court_id"] == court.id

    # Eksplicitni null odbija se s 422
    null_resp = await client.patch(
        f"/bookings/{b['id']}",
        json={"starts_at": None},
        headers=headers,
    )
    assert null_resp.status_code == 422
    assert null_resp.json()["code"] == "validation_error"
