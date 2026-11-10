# ECHO-ASSIST AI mobile client

This Flutter client uses the same FastAPI authentication and owner-scoped API
as the website. It provides login/registration, refresh-token storage, profile,
accessibility preferences, smart-cane registration, SOS, camera-frame upload,
and provider-backed navigation.

The client never invents routes or reports unconfirmed notification delivery.

## Run locally

Start the backend first:

```powershell
cd ..\echo-assist-ai\backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then run the mobile client. The Android emulator can reach a backend on the
development machine through `10.0.2.2`; replace this with an HTTPS endpoint on
a physical device or release build.

```powershell
cd ..\echo_assist_mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For a physical Android device, use the development machine's LAN address only
on a trusted network. Production builds must use HTTPS:

```powershell
flutter run --dart-define=API_BASE_URL=https://api.example.com
```

## Verification

```powershell
flutter test --no-pub
flutter analyze --no-pub
```
