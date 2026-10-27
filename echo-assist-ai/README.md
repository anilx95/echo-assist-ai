# ECHO-ASSIST AI

**AI for Inclusive Mobility**

An AI-powered smart cane companion system for visually impaired users, combining computer vision, sensor fusion, voice guidance, navigation, and emergency assistance into one accessible application.

> This README covers **Phase 1: Project structure and configuration** plus the working backend foundation, database models, sensor simulator, and mobile app skeleton. Later phases (BLE, real AI models, fall detection, navigation, etc.) are built incrementally on top of this foundation — see [Development Order](#development-order).

---

## 1. Problem Statement

Traditional white canes only detect ground-level obstacles. Existing "smart canes" are expensive and offer limited intelligence. Visually impaired users still struggle to:

- Detect obstacles above waist level
- Understand their surroundings
- Navigate unfamiliar environments safely
- Get help quickly in an emergency

## 2. Solution

ECHO-ASSIST AI combines a smartphone app, an ESP32-based smart cane, and an AI backend into one pipeline:

```
Camera Input
  → Object Detection
  → Distance Estimation
  → ESP32 Sensor Data
  → Sensor Fusion
  → Risk Prediction
  → Decision Engine
  → Voice Guidance + Vibration Alert + UI Update
```

## 3. Features (MVP scope)

| Feature | Status |
|---|---|
| Backend API (auth, contacts, sensors, AI, emergency, navigation) | ✅ Implemented |
| Database models & schema | ✅ Implemented |
| Mock AI (object detection, risk, scene description) | ✅ Implemented |
| ESP32 sensor simulator | ✅ Implemented |
| Mobile app foundation (theme, routing, home screen) | ✅ Implemented |
| Real YOLO/MiDaS models, BLE, navigation, fall detection | 🔜 Later phases |

## 4. Architecture

Clean, modular monorepo — each concern lives in its own layer so pieces (AI models, BLE, maps provider) can be swapped without touching the rest of the app.

```
echo-assist-ai/
├── mobile/            Flutter app (UI, state, services)
├── backend/           FastAPI backend (API, DB, auth, business logic)
├── ai_engine/         Modular AI interfaces (detection, depth, fusion, risk, decision)
├── esp32_firmware/    ESP32 firmware source + Python sensor simulator
├── docs/              Architecture, API, BLE protocol, hardware, demo docs
├── tests/             Cross-cutting/integration tests
├── docker-compose.yml
└── .env.example
```

## 5. Technology Stack

- **Mobile:** Flutter, Dart, Material 3, Provider, Dio, flutter_tts, speech_to_text, geolocator, flutter_blue_plus
- **Backend:** Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy, SQLite (Postgres-ready)
- **AI:** Modular interfaces for YOLO object detection, MiDaS depth estimation, sensor fusion, Random Forest risk classification — with automatic mock-mode fallback when model weights aren't available
- **Hardware:** ESP32, ultrasonic sensor, ToF sensor, MPU6050 IMU, vibration motor, SOS button

---

## 6. Installation

### Prerequisites

- Python 3.11+
- Flutter 3.19+ (for mobile development)
- Node not required for MVP

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # edit values as needed; never commit .env
uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`.

Run tests:

```bash
pytest -v
```

### Mobile Setup

```bash
cd mobile
flutter pub get
flutter run --dart-define=BACKEND_URL=http://10.0.2.2:8000   # Android emulator
# or for iOS simulator / physical device on the same network:
flutter run --dart-define=BACKEND_URL=http://<your-machine-ip>:8000
```

### AI Model Setup

The AI service defaults to **mock mode** (`AI_MOCK_MODE=true` in `.env`), which generates realistic fake detections so the whole pipeline works with zero model downloads. To use real models later, drop weights into `ai_engine/models/` and set `AI_MOCK_MODE=false` — see `ai_engine/` module docstrings for the expected interface.

### ESP32 Setup

Firmware source lives in `esp32_firmware/src/` (added in a later phase). Until real hardware is flashed, use the **sensor simulator** to generate realistic packets:

```bash
cd esp32_firmware/simulator
pip install -r requirements.txt

# Get a token first:
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Demo User","email":"demo@example.com","password":"demopass123"}'

python sensor_simulator.py --token <ACCESS_TOKEN> --scenario pole_ahead --count 10
python sensor_simulator.py --token <ACCESS_TOKEN> --scenario random --count 30 --interval 0.5
```

Available scenarios: `safe_path`, `pole_ahead`, `person_ahead`, `car_approaching`, `stairs_ahead`, `fall_detected`, `sos_pressed`, `low_battery`, `random`.

### Docker (backend only, for now)

```bash
docker compose up --build
```

---

## 7. API Endpoints (Phase 1)

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a user account |
| POST | `/auth/login` | Get access/refresh tokens |
| POST | `/auth/refresh` | Refresh an access token |
| GET/PUT | `/user/profile` | View/update profile |
| GET/POST | `/contacts` | List/add emergency contacts |
| PUT/DELETE | `/contacts/{id}` | Update/remove a contact |
| POST | `/ai/detect` | Mock/real object detection |
| POST | `/ai/risk` | Rule-based risk classification |
| POST | `/ai/scene-description` | Scene description |
| POST | `/sensors/data` | Ingest an ESP32 sensor packet |
| GET | `/sensors/latest` | Latest sensor reading for the user's device |
| POST | `/emergency/trigger` | Trigger SOS / fall event, notify contacts |
| POST | `/emergency/cancel` | Cancel an active emergency |
| GET | `/emergency/history` | List past emergency events |
| POST | `/navigation/route` | Get a route (mock mode without a maps API key) |
| GET | `/health` | Health check |

Full interactive reference: `/docs` (Swagger UI) once the backend is running.

## 8. Demo Mode

The backend runs in AI mock mode and mock-navigation mode by default — no API keys or model weights required. Combined with the sensor simulator, this lets you demo the full pipeline (sensor → risk → decision → voice/vibration message) without any physical hardware. Dedicated in-app Demo Mode controls (per section 23 of the spec) land in a later phase.

## 9. Testing

```bash
cd backend
pytest -v
```

Current coverage: app boot/DB init, registration + login, duplicate-email rejection, auth-protected routes, sensor ingestion, and risk classification. More tests (sensor fusion, fall detection, alert cooldown) are added alongside their respective phases.

## 10. Security Notes

- Passwords are hashed with bcrypt via passlib; never stored in plaintext.
- JWT access/refresh tokens; no hardcoded secrets — everything comes from `.env`.
- CORS is configured via `ALLOWED_ORIGINS` in `.env`.
- Emergency notifications use a mock provider by default (logs instead of sending real SMS/email) so the app is fully testable without third-party API keys.

## 11. Development Order

This project is being built in phases, per the master specification:

1. ✅ Project structure and configuration
2. ✅ FastAPI backend and database
3. 🔶 Flutter application UI and navigation (foundation done; more screens to come)
4. ✅ Mock sensor simulator
5. 🔜 Sensor fusion engine
6. 🔜 Rule-based risk engine (API stub exists; full `ai_engine` module next)
7. 🔜 Decision engine
8. 🔜 Voice and vibration alert system (voice service scaffolded)
9. 🔜 Camera and object detection pipeline
10. 🔜 Distance estimation
11. 🔜 BLE smart cane connection
12. 🔜 Navigation
13. 🔜 Fall detection and SOS
14. 🔜 Random Forest risk model
15. 🔜 Testing, optimization, and documentation

## 12. Future Improvements

Traffic light detection, indoor navigation, currency recognition, face recognition, scene-understanding AI, AI assistant integration, cloud analytics.

---

**ECHO-ASSIST AI** — *AI for Inclusive Mobility*
