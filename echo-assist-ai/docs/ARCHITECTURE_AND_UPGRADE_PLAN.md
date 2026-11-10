# ECHO-ASSIST AI Architecture and Upgrade Plan

## Status and scope

This document is the Phase 2 architecture decision record for the website-first
upgrade. It is based on the repository audit completed on 2026-11-07. It does
not claim that planned features are implemented.

The current FastAPI backend contains useful domain logic and is retained as the
single API. The current static dashboard will be replaced by a dedicated
responsive web client. The two Flutter applications are deferred to the future
mobile phase and will consume the same API after the backend contract is stable.

## Target architecture

```text
Browser (accessible responsive web application)
              |
              | HTTPS + short-lived JWT access token
              v
FastAPI application
  |- auth and account service
  |- profile, preferences, contacts, and notifications service
  |- device registration and sensor ingestion service
  |- obstacle-processing and history service
  |- navigation provider adapter and route-history service
  |- SOS orchestration and notification-delivery service
  |- health, audit logging, and OpenAPI endpoints
              |
              +-------------------+--------------------+
              |                   |                    |
              v                   v                    v
         PostgreSQL          Redis / job queue    Provider adapters
       (durable records)     (retries/events)   maps, email, SMS, push
              |
              v
ESP32 cane / explicit simulator mode
```

The AI inference code remains behind service interfaces. Optional models must
initialize lazily and publish readiness state; their failure must not prevent
authentication, health, SOS, or other core endpoints from starting. A normal
RGB camera must never be represented as an accurate distance source. Distance
will be labelled as sensor-fused, depth-estimated, or unavailable.

## Component boundaries

| Component | Responsibility | Persistence / external boundary |
| --- | --- | --- |
| Web client | Public site, auth UI, dashboard, accessibility settings, device/SOS/navigation controls | REST API only |
| API layer | Validation, schemas, response errors, authorization, rate limiting | FastAPI routers |
| Domain services | Ownership rules and workflows for users, cane data, detections, routes, and alerts | SQLAlchemy repositories and adapters |
| Database | Durable user-owned data, operational history, notification outcomes, audit logs | PostgreSQL + Alembic |
| Async worker | SOS retries, provider delivery attempts, device-offline evaluation, optional AI jobs | Redis-backed queue |
| AI adapters | Object detection, optional depth, segmentation, risk scoring | Local model files or isolated inference service |
| Provider adapters | Routing, geocoding, SMS, email, push | Explicitly configured third-party providers |
| IoT adapter | Authenticated device registration and sensor packet intake | ESP32 firmware protocol / simulator flag |

## Data model plan

The Phase 3 schema will use migrations and explicit foreign-key ownership:

| Table | Purpose |
| --- | --- |
| users | Identity, password hash, role, verification and account state |
| user_profiles | Optional name, phone, photo reference, birth date, address, medical/accessibility details |
| user_preferences | Voice, display, language, accessibility and emergency preferences |
| emergency_contacts | User-owned contacts and verified delivery channels |
| devices | Device identity, owner, firmware, credentials/status, latest health summary |
| device_sensor_readings | Timestamped sensor data, source and validation state |
| obstacle_detection_history | Detection, confidence, risk, distance provenance and session metadata |
| navigation_history | Provider route, coordinates, progress and status |
| sos_alerts | Alert lifecycle, valid location, deduplication key, resolution and escalation state |
| notification_deliveries | Per-channel provider attempt, provider ID, confirmed outcome, failure/retry data |
| system_logs | Structured audit and operational events with sensitivity controls |
| refresh_sessions | Refresh-token/session lifecycle and revocation data |

## Key engineering decisions

1. Keep FastAPI and SQLAlchemy. Introduce PostgreSQL, Alembic, and a PostgreSQL driver rather than replacing the backend stack.
2. Build a separate website frontend; do not continue mobile application development in this phase.
3. Preserve existing AI assets, but make startup resilient and distinguish mock, live, failed, and unavailable states in API responses and the UI.
4. Make notification success provider-confirmed only. Simulator activity and mock notification activity must be labelled as simulated and never as delivered.
5. Use a durable queue for retries and delayed SOS escalation; in-process sleep and global state are unsuitable for production.
6. Enforce owner-scoped database access in every private endpoint and reserve roles for future support/admin functions.
7. Use provider adapters rather than embedding maps, SMS, email, or push logic directly in routers.

## Delivery sequence

1. Stabilize configuration, dependency manifests, runtime startup, and testing baseline.
2. Introduce PostgreSQL, Alembic migrations, health checks, and data-model normalization.
3. Complete account management: secure sessions, logout/revocation, password reset, verification where configured, profile and preferences.
4. Normalize REST contracts, error handling, rate limiting, audit logging, and dashboard endpoints.
5. Harden AI/image processing and persist appropriately labelled detection history.
6. Implement SOS lifecycle, delivery outcomes, retries, duplicate protection, and hardware-trigger flow.
7. Implement navigation provider integration with live route history; reject requests when no provider is configured.
8. Implement device registration, ingestion authentication, device health, offline monitoring, and simulator separation.
9. Build and test the accessible website against the completed API.
10. Complete Docker Compose, end-to-end tests, operational documentation, and deployment checks.

## Non-goals for this release

- Android or iOS application delivery.
- Claims of medical emergency detection, collision prevention, or camera-only metric distance accuracy.
- Simulated telemetry or routes presented as real-world readings or directions.

## Acceptance gates

Each implementation phase must report changed files, executed tests, known limitations,
and uncompleted work. A feature is not marked complete until it has an automated test
or an explicitly documented manual verification procedure.
