# PadelHub

Sustav za rezervaciju padel terena i organizaciju javnih otvorenih mečeva, izrađen u sklopu kolegija **Programiranje za web** na SIT UNIZD.

Voditelj centra upravlja terenima i nadzire sve termine, a igrači rezerviraju privatne termine ili otvaraju mečeve kojima se drugi igrači odgovarajuće razine igre mogu priključiti do popune kapaciteta (`2` ili `4` igrača).

## Struktura

```
api/                 # backend: FastAPI
  app/
    main.py          # sastavljanje aplikacije
    core/            # konfiguracija, ovisnosti, pogreške, faze, raspored
    routers/         # rute: primaju zahtjev, vraćaju odgovor
    schemas/         # Pydantic sheme ulaza i izlaza
    services/        # poslovna pravila
    repositories/    # upiti nad bazom
    models/          # SQLAlchemy modeli
web/                 # frontend: dolazi u 2. dijelu
docker-compose.yml   # baza podataka (PostgreSQL 16)
.env.example         # predložak konfiguracije
```

## Preduvjeti

- Git
- Python 3.11 ili noviji
- [uv](https://docs.astral.sh/uv/)
- Docker s alatom Docker Compose

## Pokretanje

```bash
# 1) Konfiguracija
cp .env.example .env

# 2) Baza
docker compose up -d db

# 3) Backend
cd api
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Provjera:

- http://127.0.0.1:8000/health/ vraća `{"status": "ok"}`
- http://127.0.0.1:8000/docs prikazuje Swagger UI s popisom ruta

## Baza podataka

Shema baze mijenja se isključivo migracijama u `api/alembic/versions/` (`001` – `003`).

```bash
cd api
alembic upgrade head      # primijeni sve migracije
alembic downgrade -1      # poništi zadnju migraciju
alembic current           # trenutna migracija
```

### Početni podatci

`python -m app.seed` stvara voditelja centra, pet igrača, četiri padel terena i tri termina. Skripta je idempotentna i smije se pokrenuti više puta.

| Uloga | Korisničko ime | Lozinka | Razina (`skill_level`) |
|-------|----------------|---------|------------------------|
| `admin` | `admin@padel.hr` | `admin123` | `5.0` |
| `player` | `ivan@padel.hr` | `player123` | `3.5` |
| `player` | `ana@padel.hr` | `player123` | `4.0` |
| `player` | `marko@padel.hr` | `player123` | `3.0` |
| `player` | `petra@padel.hr` | `player123` | `4.5` |
| `player` | `luka@padel.hr` | `player123` | `2.5` |

### Prazna baza

```bash
docker compose down -v
docker compose up -d db
cd api
alembic upgrade head
python -m app.seed
```

## Testovi

```bash
docker compose up -d db
cd api
pytest -v
```

Testovi rade nad zasebnom bazom `padel_hub_test` na istom poslužitelju, a tablice se prazne prije svakog testa.

## Kvaliteta koda

```bash
cd api
ruff format .
ruff check .
```

## API

Svi popisi primaju `limit` i `offset` (zadano `20`, najviše `100`). Access token vrijedi 15 minuta, refresh token 7 dana, a šalje se u zaglavlju `Authorization: Bearer <token>`.

### Autentikacija

| Metoda | Putanja | Opis | Pristup |
|--------|---------|------|---------|
| POST | `/auth/login` | prijava, vraća `access_token` i `refresh_token` | javno |
| POST | `/auth/refresh` | novi par tokena na temelju `refresh_token`-a | javno |
| GET | `/auth/me` | profil prijavljenog korisnika | prijavljen |

### Tereni

| Metoda | Putanja | Opis | Pristup |
|--------|---------|------|---------|
| GET | `/courts/` | popis terena, filtar `surface` | prijavljen |
| POST | `/courts/` | novi teren | `admin` |
| GET | `/courts/{court_id}` | detalji terena | prijavljen |
| PATCH | `/courts/{court_id}` | djelomična izmjena terena | `admin` |
| DELETE | `/courts/{court_id}` | brisanje terena ako nema rezervacija | `admin` |
| GET | `/courts/{court_id}/availability` | zauzeti termini za zadani `day` | prijavljen |

### Rezervacije

| Metoda | Putanja | Opis | Pristup |
|--------|---------|------|---------|
| GET | `/bookings/` | popis rezervacija (`court_id`, `booking_type`, `status`) | `admin`: sve, `player`: svoje |
| POST | `/bookings/` | nova privatna rezervacija ili otvoreni meč | prijavljen |
| GET | `/bookings/{booking_id}` | detalji rezervacije | `admin`, vlasnik |
| PATCH | `/bookings/{booking_id}` | izmjena rezervacije u fazi `open_change` | `admin`, vlasnik |
| POST | `/bookings/{booking_id}/cancel` | otkazivanje rezervacije u fazi `open_change` | `admin`, vlasnik |

### Otvoreni mečevi

| Metoda | Putanja | Opis | Pristup |
|--------|---------|------|---------|
| GET | `/matches/` | popis javnih otvorenih mečeva (`court_id`, `status`, `upcoming_only`) | prijavljen |
| GET | `/matches/{match_id}` | detalji otvorenog meča i popis sudionika | prijavljen |
| POST | `/matches/{match_id}/join` | prijava u meč u fazi `open_change` ili `locked` | prijavljen |
| POST | `/matches/{match_id}/leave` | odjava iz meča u fazi `open_change` | sudionik (osim kreatora) |

## Faze termina i poslovna pravila

Faza termina ne pohranjuje se u bazu nego se računa pri svakom zahtjevu u `app/core/phases.py` (`cancellation_deadline` postavlja se automatski na 6 sati prije `starts_at`; ako se termin stvori ili pomakne na manje od 6 sati unaprijed, odmah je u fazi `locked`).

| Radnja | `open_change` | `locked` | `started` |
|--------|:-------------:|:--------:|:---------:|
| čitanje termina i mečeva | da | da | da |
| izmjena (`PATCH`) i otkazivanje (`/cancel`) | da | ne | ne |
| prijava u otvoreni meč (`/join`) | da | da | ne |
| odjava iz otvorenog meča (`/leave`) | da | ne | ne |

Dodatna pravila:

- **Raspored za igrače:** radno vrijeme `09:00–23:00` (`Europe/Zagreb`), početak na `:00` ili `:30`, trajanje `60`, `90` ili `120` minuta, zabrana ostavljanja neiskoristive rupe kraće od 60 minuta (`unusable_gap_left`) te zatvoreno na Božić (`25.12.`), Staru godinu (`31.12.`), Novu godinu (`01.01.`) i Uskrs.
- **Preklapanje i kapacitet:** aktivni termini na istom terenu ne smiju se preklapati (`slot_conflict`), a otvoreni meč prima najviše `max_players` (`2` ili `4`) igrača čija je razina unutar `[min_level, max_level]`.

## Pogreške

Svaki neuspjeh vraća tijelo istoga oblika:

```json
{ "code": "not_found", "message": "Teren nije pronađen" }
```

Odgovor `422` uz to sadrži polje `errors` s popisom neispravnih polja.

| `code` | HTTP | Kada |
|--------|------|------|
| `validation_error` | 422 | tijelo ili parametri ne odgovaraju shemi |
| `invalid_credentials` | 401 | prijava ili token ne vrijede |
| `token_expired` | 401 | pristupni ili refresh token je istekao |
| `forbidden` | 403 | uloga ili vlasništvo ne dopuštaju radnju |
| `not_found` | 404 | traženi zapis ili ruta ne postoji |
| `method_not_allowed` | 405 | HTTP metoda nije podržana na ruti |
| `duplicate` | 409 | već postoji teren s tim nazivom |
| `has_bookings` | 409 | teren ima rezervacije i ne može se obrisati |
| `slot_conflict` | 409 | termin na terenu preklapa se s postojećim |
| `already_joined` | 409 | igrač je već prijavljen u taj otvoreni meč |
| `match_full` | 409 | otvoreni meč je već popunjen |
| `slot_in_past` | 400 | početak termina je u prošlosti |
| `outside_working_hours` | 400 | termin prelazi izvan radnog vremena `09:00–23:00` |
| `club_closed_holiday` | 400 | klub ne radi na odabrani blagdan |
| `invalid_slot_alignment` | 400 | početak termina nije na `:00` ili `:30` |
| `invalid_slot_duration` | 400 | trajanje termina nije `60`, `90` ili `120` minuta |
| `unusable_gap_left` | 400 | rezervacija ostavlja rupu kraću od 60 minuta |
| `deadline_passed` | 400 | istekao je rok za izmjenu, otkazivanje ili odjavu |
| `booking_cancelled` | 400 | otkazana rezervacija ne može se mijenjati |
| `already_cancelled` | 400 | rezervacija je već otkazana |
| `invalid_time_range` | 400 | početak termina nije prije kraja (pri `PATCH` izmjeni) |
| `invalid_level_range` | 400 | minimalna razina veća je od maksimalne (pri `PATCH` izmjeni) |
| `capacity_too_low` | 400 | novi kapacitet manji je od broja već prijavljenih igrača |
| `match_cancelled` | 400 | otvoreni meč je otkazan |
| `match_started` | 400 | otvoreni meč je već počeo |
| `skill_out_of_range` | 400 | razina igre korisnika je izvan raspona meča |
| `creator_cannot_leave` | 400 | kreator meča mora otkazati termin umjesto odjave |
| `not_a_participant` | 400 | korisnik nije aktivni sudionik meča |
