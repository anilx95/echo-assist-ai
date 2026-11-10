# ECHO-ASSIST AI

ECHO-ASSIST AI is a website-first smart-cane assistance platform. It provides
an accessible web dashboard, FastAPI REST API, PostgreSQL migrations, smart
cane/sensor integration, optional vision processing, navigation, and SOS flows.
Future mobile clients can consume the same authenticated API.

> Safety notice: this software does not guarantee obstacle avoidance, medical
> emergency detection, collision prevention, or emergency-contact delivery.
> Camera detections are not represented as validated metric distance.

## Architecture

```text
Accessible browser UI -> FastAPI API -> PostgreSQL
                         |      |      |
                    AI adapters  SOS/notifications  device sensor intake
                         |
                    ESP32 hardware or labelled simulator
```

The browser UI is served by FastAPI at `/`. See the
[architecture decision record](docs/ARCHITECTURE_AND_UPGRADE_PLAN.md).

## Implemented features

- Registration, login, refresh-token rotation, revocable logout sessions, and
  one-time password-reset and email-verification tokens.
- Owner-scoped profiles, preferences, contacts, devices, sensor readings,
  dashboard data, detection history, notification history, and SOS records.
- PostgreSQL-ready SQLAlchemy models and Alembic migrations.
- Explicit simulator device labels and provider delivery outcomes. A mock
  notification is recorded as `not_delivered`, never as a real delivery.
- Optional YOLO, MiDaS, Fast-SCNN, and Whisper services load lazily, so model
  failures do not block core account or SOS APIs.
- OpenAPI docs at `/docs`, database-aware `/health`, a basic single-process
  rate limit, and responsive keyboard-friendly UI at `/`.

## Known limits

- Durable job retries, distributed rate limiting, and ESP32 firmware source
  remain future work.
- SMS, email, push, and live routes require configured providers. Their mock
  modes are clearly labelled and never claimed as real delivery; navigation
  requests are rejected rather than simulated when no routing provider exists.
- Realtime AI state is per-process; multi-worker deployments need Redis.
- Docker was not executed here because Docker is unavailable in this workspace.

## Local development

Requirements: Python 3.11+ and PostgreSQL 16+ (or Docker).

```powershell
cd echo-assist-ai/backend
Copy-Item .env.example .env
# Set DATABASE_URL, SECRET_KEY, and optional provider credentials.
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` for the website and `/docs` for API docs. SQLite
is configured only by automated tests; application runtime uses PostgreSQL.

## Docker

```bash
cd echo-assist-ai
cp backend/.env.example backend/.env
# Set SECRET_KEY and a non-example POSTGRES_PASSWORD before deployment.
docker compose up --build
```

Compose starts PostgreSQL as `db`, waits for it to become healthy, migrates the
database, and starts the API/UI on port 8000. Data persists in
`echo_assist_postgres_data`.

## Hardware simulator

```powershell
cd esp32_firmware/simulator
pip install -r requirements.txt
python sensor_simulator.py --token <access-token> --scenario pole_ahead
```

The simulator registers an explicitly simulated device; it is never displayed
as physical hardware.

## Testing

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\alembic.exe check
```

Automated tests cover migration setup, auth, profile updates, session revocation,
preferences, device registration, sensor ingestion, and risk classification.
