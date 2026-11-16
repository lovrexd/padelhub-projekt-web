# PadelHub — Rezervacija padel terena i otvoreni mečevi

Projekt iz kolegija **Programiranje za web** (SIT UNIZD).

Sustav omogućuje voditelju padel centra (`admin`) upravljanje terenima i pregled svih termina, a igračima (`player`) privatne rezervacije terena te kreiranje i pridruživanje otvorenim mečevima s provjerom preklapanja termina, kapaciteta, razine igre i roka otkazivanja.

---

## Brzi linkovi (kad je poslužitelj pokrenut)

- Swagger UI (interaktivno testiranje ruta): http://127.0.0.1:8000/docs
- ReDoc dokumentacija: http://127.0.0.1:8000/redoc
- Provjera rada API-ja: http://127.0.0.1:8000/health/

---

## Struktura projekta

```text
api/                 # backend: FastAPI
  app/
    main.py          # sastavljanje aplikacije i registracija ruta
    core/            # konfiguracija (.env), baza, JWT, bcrypt, pogreške, ovisnosti
    routers/         # rute: primaju HTTP zahtjev i vraćaju odgovor
    schemas/         # Pydantic sheme ulaza i izlaza
    services/        # poslovna pravila i provjere vlasništva
    repositories/    # SQLAlchemy upiti prema bazi podataka
    models/          # ORM modeli tablica u PostgreSQL-u
    seed.py          # idempotentna skripta za početne podatke
  alembic/           # migracije sheme baze podataka
  tests/             # pytest testovi nad zasebnom bazom padel_hub_test
web/                 # frontend: Vue 3 (dolazi u 2. dijelu projekta)
docker-compose.yml   # PostgreSQL 16 baza podataka
.env.example         # predložak konfiguracije (bez pravih tajni)
```

---

## Preduvjeti

- Git
- Python 3.12 (ili noviji)
- [uv](https://docs.astral.sh/uv/)
- Docker s alatom Docker Compose

---

## Prvo pokretanje (od nule)

```bash
# 1) Konfiguracija (iz glavne mape projekta)
cp .env.example .env

# 2) Pokretanje PostgreSQL baze podataka
docker compose up -d db

# 3) Virtualno okruženje i paketi
cd api
uv venv --python 3.12
uv pip install -r requirements.txt

# 4) Aktivacija okruženja (odaberi prema svom terminalu)
source .venv/bin/activate         # bash / zsh
source .venv/bin/activate.fish    # fish

# 5) Tablice i početni podatci
alembic upgrade head
python -m app.seed

# 6) Pokretanje backend poslužitelja
uvicorn app.main:app --reload
```

---

## Svakodnevne naredbe (iz mape `api/`)

Ako koristiš aktivirano okruženje (`source .venv/bin/activate.fish`), naredbe pokrećeš izravno; inače samo ispred dodaj `.venv/bin/` (npr. `.venv/bin/pytest -v`).

```bash
# Pokretanje API poslužitelja
uvicorn app.main:app --reload

# Pokretanje svih testova (koristi bazu padel_hub_test)
pytest -v

# Provjera stila i formatiranja koda
ruff check .
ruff format --check .
```

### Korisne naredbe za bazu i migracije

```bash
cd api
alembic current           # prikaz trenutne migracije u bazi
alembic upgrade head      # primijeni sve migracije do najnovije
alembic downgrade -1      # vrati jednu migraciju unatrag
python -m app.seed        # ponovno punjenje početnih podataka (ne stvara duplikate)
```

Za potpuno resetiranje baze iz glavne mape projekta:

```bash
docker compose down -v
docker compose up -d db
cd api
alembic upgrade head
python -m app.seed
```

---

## Početni korisnički računi (`python -m app.seed`)

| Uloga | Korisničko ime | Lozinka | Razina igre |
|-------|----------------|---------|-------------|
| `admin` | `admin@padel.hr` | `admin123` | 5.0 |
| `player` | `ivan@padel.hr` | `player123` | 3.5 |
| `player` | `ana@padel.hr` | `player123` | 4.0 |
| `player` | `marko@padel.hr` | `player123` | 3.0 |
| `player` | `petra@padel.hr` | `player123` | 4.5 |
| `player` | `luka@padel.hr` | `player123` | 2.5 |

*(Tablice krajnjih točaka, poslovnih pravila i kodova pogrešaka dodajemo kako dovršavamo preostale module.)*
