# PadelHub — Rezervacija padel terena i otvoreni mečevi

Projekt iz kolegija **Programiranje za web** (SIT UNIZD).

Sustav omogućuje voditelju padel centra (`admin`) upravljanje terenima i pregled svih termina, a igračima (`player`) privatne rezervacije terena te kreiranje i pridruživanje otvorenim mečevima s dinamičkim računanjem vremenske faze, provjerom preklapanja termina, kapaciteta, razine igre i roka otkazivanja.

---

## Brzi linkovi (kad je poslužitelj pokrenut)

- Swagger UI (interaktivno testiranje ruta): http://127.0.0.1:8000/docs
- Provjera rada API-ja: http://127.0.0.1:8000/health/

---

## Struktura projekta

```text
api/                 # backend: FastAPI
  app/
    main.py          # sastavljanje aplikacije i registracija ruta
    core/            # konfiguracija (.env), baza, JWT, bcrypt, faze, pogreške, ovisnosti
    routers/         # rute: primaju HTTP zahtjev, provjeravaju ulogu i vraćaju odgovor
    schemas/         # Pydantic sheme ulaza, djelomične izmjene (PATCH) i izlaza
    services/        # poslovna pravila, vlasništvo i prevođenje grešaka
    repositories/    # SQLAlchemy upiti prema bazi podataka
    models/          # ORM modeli tablica u PostgreSQL-u
    seed.py          # idempotentna skripta za početne podatke
  alembic/           # migracije sheme baze podataka (001-003)
  tests/             # pytest testovi nad zasebnom bazom padel_hub_test
web/                 # frontend: Vue 3 (dolazi u 2. dijelu projekta)
docker-compose.yml   # PostgreSQL 16 baza podataka
.env.example         # predložak konfiguracije (bez pravih tajni)
```

---

## Svakodnevno pokretanje

```bash
# 1) Pokreni PostgreSQL kontejner (iz glavne mape projekta)
docker compose up -d db

# 2) Uđi u api/ i aktiviraj postojeće virtualno okruženje
cd api
source .venv/bin/activate.fish    # ako koristiš bash/zsh: source .venv/bin/activate

# 3) Pokreni backend poslužitelj
uvicorn app.main:app --reload
```

Kad je okruženje `(api)` aktivirano, izravno pokrećeš i provjere:

```bash
pytest -v                # pokretanje svih testova (nad padel_hub_test)
ruff check .             # provjera grešaka i stila
ruff format --check .    # provjera formatiranja
```

*(Ako ne želiš aktivirati okruženje, ispred svake naredbe u `api/` samo dodaj `.venv/bin/`, npr. `.venv/bin/uvicorn app.main:app --reload` ili `.venv/bin/pytest -v`.)*

---

## Prvo pokretanje (samo JEDNOM)

Ove korake izvodiš samo kad prvi put preuzimaš projekt na računalo:

```bash
# 1) Kopiraj konfiguraciju (iz glavne mape projekta)
cp .env.example .env              # PowerShell: Copy-Item .env.example .env

# 2) Pokreni bazu podataka
docker compose up -d db

# 3) Napravi virtualno okruženje i instaliraj pakete
cd api
uv venv --python 3.12
source .venv/bin/activate.fish    # bash/zsh: source .venv/bin/activate
uv pip install -r requirements.txt

# 4) Stvori tablice i početne podatke
alembic upgrade head
python -m app.seed

# 5) Pokreni backend poslužitelj
uvicorn app.main:app --reload
```

### Preduvjeti

- Git
- Python 3.12 (ili noviji)
- [uv](https://docs.astral.sh/uv/)
- Docker s alatom Docker Compose

---

## Baza podataka i migracije (`api/`)

Shema baze mijenja se isključivo Alembic migracijama u `api/alembic/versions/`:

```bash
cd api
alembic current           # trenutna verzija sheme u bazi
alembic upgrade head      # primijeni sve migracije do najnovije
alembic downgrade -1      # vrati zadnju migraciju unatrag
python -m app.seed        # početni podatci (idempotentno — ne stvara duplikate)
```

Za potpuno brisanje i ponovno punjenje razvojne baze iz glavne mape projekta:

```bash
docker compose down -v
docker compose up -d db
cd api
alembic upgrade head
python -m app.seed
```

### Početni podatci (`python -m app.seed`)

Skripta upisuje voditelja centra, pet igrača različitih razina igre, četiri padel terena te tri buduća termina za dan `14.03.2027.` (privatnu rezervaciju, polu-popunjen otvoreni meč `2/4` za razinu `3.0–5.0` i već popunjen otvoreni meč `4/4`):

| Uloga | Korisničko ime | Lozinka | Razina igre |
|-------|----------------|---------|-------------|
| `admin` | `admin@padel.hr` | `admin123` | 5.0 |
| `player` | `ivan@padel.hr` | `player123` | 3.5 |
| `player` | `ana@padel.hr` | `player123` | 4.0 |
| `player` | `marko@padel.hr` | `player123` | 3.0 |
| `player` | `petra@padel.hr` | `player123` | 4.5 |
| `player` | `luka@padel.hr` | `player123` | 2.5 |

---

## Krajnje točke (20 ruta)

Svi popisi primaju parametre straničenja `limit` (zadano `20`, najviše `100`) i `offset` (zadano `0`).

| Metoda | Putanja | Uloge | Vlasništvo / napomena |
|--------|---------|-------|-----------------------|
| `GET` | `/health/` | javno | Provjera rada API-ja |
| `POST` | `/auth/login` | javno | Prijava; vraća `access_token` (15 min) i `refresh_token` (7 dana) |
| `POST` | `/auth/refresh` | javno | Izdaje novi par tokena na temelju valjanog `refresh_token`-a |
| `GET` | `/auth/me` | `admin`, `player` | Profil prijavljenog korisnika (bez `password_hash`) |
| `GET` | `/courts/` | `admin`, `player` | Popis terena (`surface`, `limit`, `offset`) |
| `POST` | `/courts/` | `admin` | Dodavanje novog terena (`UNIQUE` naziv -> `409 duplicate`) |
| `GET` | `/courts/{court_id}` | `admin`, `player` | Detalji terena |
| `PATCH` | `/courts/{court_id}` | `admin` | Djelomična izmjena terena |
| `DELETE` | `/courts/{court_id}` | `admin` | Brisanje terena ako nema rezervacija (`409 has_bookings`) |
| `GET` | `/courts/{court_id}/availability` | `admin`, `player` | Zauzeti termini na terenu za `day` (bez osobnih podataka) |
| `GET` | `/bookings/` | `admin`, `player` | `admin` vidi sve; `player` isključivo vlastite rezervacije |
| `POST` | `/bookings/` | `admin`, `player` | Nova privatna rezervacija ili otvoreni meč (kreator ulazi kao 1/N) |
| `GET` | `/bookings/{booking_id}` | `admin`, `player` | Detalji rezervacije (`403` ako `player` gleda tuđu) |
| `PATCH` | `/bookings/{booking_id}` | `admin`, `player` | Izmjena vlastite rezervacije u fazi `open_change` |
| `POST` | `/bookings/{booking_id}/cancel` | `admin`, `player` | Meko otkazivanje (`status = cancelled`) u fazi `open_change` |
| `POST` | `/bookings/{booking_id}/reactivate` | `admin`, `player` | Ponovna aktivacija ako rok nije prošao i termin je slobodan |
| `GET` | `/matches/` | `admin`, `player` | Popis javnih otvorenih mečeva (`court_id`, `status`, `upcoming_only`) |
| `GET` | `/matches/{match_id}` | `admin`, `player` | Detalji otvorenog meča s popisom aktivnih igrača (`404` za privatne) |
| `POST` | `/matches/{match_id}/join` | `admin`, `player` | Prijava u otvoreni meč (`open_change` i `locked`, do popune kapaciteta) |
| `POST` | `/matches/{match_id}/leave` | `admin`, `player` | Odjava iz otvorenog meča (samo u fazi `open_change`, ne za kreatora) |

---

## Poslovna pravila i vremenske faze

Faza termina (`app/core/phases.py`) ne sprema se u bazu nego se računa pri svakom zahtjevu iz UTC vremena (`cancellation_deadline` zadano je 24h prije `starts_at`):

| Radnja | `open_change` (do roka otkazivanja) | `locked` (od roka do početka) | `started` (od početka nadalje) |
|--------|--------------------------------------|-------------------------------|--------------------------------|
| Čitanje termina i mečeva | dopušteno | dopušteno | dopušteno |
| Izmjena rezervacije (`PATCH`), otkaz, reaktivacija | dopušteno | zabranjeno (`400`) | zabranjeno (`400`) |
| Prijava u otvoreni meč (`/matches/{id}/join`) | dopušteno | dopušteno | zabranjeno (`400`) |
| Odjava iz otvorenog meča (`/matches/{id}/leave`) | dopušteno | zabranjeno (`400`) | zabranjeno (`400`) |

Dodatna pravila koja provodi backend (i ograničenja u bazi):
- **Zabrana preklapanja termina:** na istom terenu aktivne rezervacije ne smiju se preklapati (`409 slot_conflict`).
- **Kapacitet i jedinstvenost:** otvoreni meč prima do `max_players` (`2` ili `4`) aktivnih igrača (`409 match_full`), a `UNIQUE (booking_id, player_id)` sprječava dvostruku prijavu istog igrača (`409 already_joined`).
- **Razina igre:** igrač može ući u otvoreni meč samo ako mu je `skill_level` unutar `[min_level, max_level]` (`400 skill_out_of_range`).
- **Brisanje terena:** teren koji ima postojeće rezervacije ne može se obrisati (`409 has_bookings`).

---

## Kodovi pogrešaka (`code`)

Svaka pogreška vraća JSON oblik `{"code": "...", "message": "..."}`, a `422` uz to sadrži i polje `errors` s popisom neispravnih polja.

| HTTP status | `code` | Značenje |
|-------------|--------|----------|
| `400` | `slot_in_past` | Odabrani početak termina je u prošlosti |
| `400` | `deadline_passed` | Istekao je rok za izmjenu, otkazivanje, reaktivaciju ili odjavu |
| `400` | `booking_cancelled` | Otkazana rezervacija ne može se uređivati prije reaktivacije |
| `400` | `invalid_time_range` | Početak termina mora biti prije kraja |
| `400` | `invalid_deadlines` | Rok za otkazivanje ne može biti nakon početka termina |
| `400` | `invalid_level_range` | Minimalna razina ne smije biti veća od maksimalne |
| `400` | `capacity_too_low` | Novi kapacitet manji je od broja već prijavljenih igrača |
| `400` | `already_cancelled` | Rezervacija je već otkazana |
| `400` | `already_active` | Rezervacija je već aktivna |
| `400` | `match_cancelled` | Otvoreni meč je otkazan |
| `400` | `match_started` | Otvoreni meč je već počeo i prijava više nije moguća |
| `400` | `skill_out_of_range` | Razina igre korisnika ne odgovara rasponu meča |
| `400` | `creator_cannot_leave` | Kreator meča mora otkazati termin na `/bookings/{id}/cancel` |
| `400` | `not_a_participant` | Korisnik nije aktivan sudionik meča |
| `401` | `invalid_credentials` | Neispravno korisničko ime, lozinka, neaktivan račun ili neispravan token |
| `401` | `token_expired` | Pristupni ili refresh token je istekao |
| `403` | `forbidden` | Nedovoljna uloga ili pokušaj pristupa tuđem zapisu |
| `404` | `not_found` | Traženi zapis ili ruta ne postoji |
| `405` | `method_not_allowed` | HTTP metoda nije podržana na toj ruti |
| `409` | `duplicate` | Već postoji teren s tim nazivom |
| `409` | `has_bookings` | Teren ima postojeće rezervacije i ne može se obrisati |
| `409` | `slot_conflict` | Termin na odabranom terenu preklapa se s postojećim aktivnim terminom |
| `409` | `already_joined` | Igrač je već prijavljen u taj otvoreni meč |
| `409` | `match_full` | Otvoreni meč je već dosegao `max_players` |
| `422` | `validation_error` | Neispravan oblik podataka ili poslana vrijednost `null` na `PATCH` |
