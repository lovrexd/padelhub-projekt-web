from datetime import datetime, timedelta, timezone

from app.models import Booking, Court
from tests.conftest import auth_header


async def test_player_cannot_create_or_update_court(client, player_user, court):
    headers = await auth_header(client, "player1", "player123")
    create_resp = await client.post(
        "/courts/",
        json={"name": "Novi teren", "surface": "outdoor", "hourly_rate": 25},
        headers=headers,
    )
    assert create_resp.status_code == 403
    assert create_resp.json()["code"] == "forbidden"

    patch_resp = await client.patch(
        f"/courts/{court.id}",
        json={"hourly_rate": 50},
        headers=headers,
    )
    assert patch_resp.status_code == 403
    assert patch_resp.json()["code"] == "forbidden"


async def test_admin_creates_lists_and_updates_court(
    client, db, admin_user, player_user
):
    admin_headers = await auth_header(client, "testadmin", "admin123")
    player_headers = await auth_header(client, "player1", "player123")

    r1 = await client.post(
        "/courts/",
        json={"name": "Teren A", "surface": "indoor", "hourly_rate": 35},
        headers=admin_headers,
    )
    assert r1.status_code == 201
    court_id = r1.json()["id"]

    # Dupli naziv terena odbija UNIQUE u bazi i prevodi se u 409
    dup = await client.post(
        "/courts/",
        json={"name": "Teren A", "surface": "outdoor", "hourly_rate": 30},
        headers=admin_headers,
    )
    assert dup.status_code == 409
    assert dup.json()["code"] == "duplicate"

    # Dodaj još dva terena za provjeru paginacije
    await client.post(
        "/courts/",
        json={"name": "Teren B", "surface": "outdoor", "hourly_rate": 28},
        headers=admin_headers,
    )
    await client.post(
        "/courts/",
        json={"name": "Teren C", "surface": "indoor", "hourly_rate": 40},
        headers=admin_headers,
    )

    page = await client.get("/courts/?limit=2&offset=1", headers=player_headers)
    assert page.status_code == 200
    assert [c["name"] for c in page.json()] == ["Teren B", "Teren C"]

    # PATCH dira samo poslano polje, a null odbija s 422
    patch_ok = await client.patch(
        f"/courts/{court_id}",
        json={"hourly_rate": 38},
        headers=admin_headers,
    )
    assert patch_ok.status_code == 200
    assert patch_ok.json()["name"] == "Teren A"
    assert patch_ok.json()["hourly_rate"] == 38

    patch_null = await client.patch(
        f"/courts/{court_id}",
        json={"name": None},
        headers=admin_headers,
    )
    assert patch_null.status_code == 422
    assert patch_null.json()["code"] == "validation_error"


async def test_court_availability_shows_active_slots_without_user_data(
    client, db, court, player_user
):
    headers = await auth_header(client, "player1", "player123")
    start = datetime(2026, 12, 10, 17, 0, tzinfo=timezone.utc)
    db.add_all(
        [
            Booking(
                court_id=court.id,
                creator_id=player_user.id,
                booking_type="private",
                starts_at=start,
                ends_at=start + timedelta(minutes=90),
                cancellation_deadline=start - timedelta(hours=24),
            ),
            Booking(
                court_id=court.id,
                creator_id=player_user.id,
                booking_type="open_match",
                starts_at=start + timedelta(hours=2),
                ends_at=start + timedelta(hours=3),
                cancellation_deadline=start - timedelta(hours=22),
                status="cancelled",
            ),
        ]
    )
    await db.commit()

    resp = await client.get(
        f"/courts/{court.id}/availability?day=2026-12-10",
        headers=headers,
    )
    assert resp.status_code == 200
    slots = resp.json()
    assert len(slots) == 1
    assert slots[0]["booking_type"] == "private"
    assert "creator_id" not in slots[0]


async def test_get_missing_court_returns_404(client, player_user):
    headers = await auth_header(client, "player1", "player123")
    resp = await client.get("/courts/999", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == "not_found"


async def test_filter_courts_by_surface(client, db, player_user):
    db.add_all(
        [
            Court(name="Unutarnji", surface="indoor", hourly_rate=35),
            Court(name="Vanjski", surface="outdoor", hourly_rate=25),
        ]
    )
    await db.commit()
    headers = await auth_header(client, "player1", "player123")
    resp = await client.get("/courts/?surface=outdoor", headers=headers)
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json()] == ["Vanjski"]
