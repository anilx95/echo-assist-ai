"""
ECHO-CANE Sensor Simulator.

Generates realistic ESP32 smart cane sensor packets and posts them to the
backend /sensors/data endpoint. Used for development and hackathon demos
when physical hardware is unavailable (see master prompt section 9 and 23).

Usage:
    python sensor_simulator.py --token <ACCESS_TOKEN> --scenario pole_ahead
    python sensor_simulator.py --token <ACCESS_TOKEN> --scenario random --count 20

Scenarios:
    safe_path       - clear path, large distances, no danger
    pole_ahead      - static obstacle at ~1.2m directly ahead
    person_ahead    - a person a few meters ahead
    car_approaching - fast obstacle approaching from the side
    stairs_ahead    - drop-off / stairs detected close by
    fall_detected   - a sudden acceleration spike simulating a fall
    sos_pressed     - the SOS button is pressed on the cane
    low_battery     - battery running low
    random          - randomly cycles through the above scenarios
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass, field

import httpx

DEFAULT_BACKEND_URL = "http://127.0.0.1:8000"
DEVICE_ID = "ECHO_CANE_001"

SCENARIOS = [
    "safe_path",
    "pole_ahead",
    "person_ahead",
    "car_approaching",
    "stairs_ahead",
    "fall_detected",
    "sos_pressed",
    "low_battery",
]


@dataclass
class SimulatorState:
    battery_percent: float = 82.0
    tick: int = 0


def _base_packet(state: SimulatorState) -> dict:
    """Baseline packet representing an idle/normal state."""
    return {
        "device_id": DEVICE_ID,
        "ultrasonic_cm": round(random.uniform(300, 500), 1),
        "tof_mm": round(random.uniform(3000, 6000), 1),
        "accel_x": round(random.uniform(-0.2, 0.2), 3),
        "accel_y": round(random.uniform(9.3, 9.9), 3),  # gravity, cane held upright
        "accel_z": round(random.uniform(-0.2, 0.2), 3),
        "gyro_x": round(random.uniform(-1, 1), 2),
        "gyro_y": round(random.uniform(-1, 1), 2),
        "gyro_z": round(random.uniform(-1, 1), 2),
        "sos_pressed": False,
        "battery_percent": round(state.battery_percent, 1),
        "timestamp": int(time.time()),
    }


def generate_packet(scenario: str, state: SimulatorState) -> dict:
    packet = _base_packet(state)

    if scenario == "safe_path":
        pass  # baseline is already a clear path

    elif scenario == "pole_ahead":
        packet["ultrasonic_cm"] = round(random.uniform(105, 130), 1)
        packet["tof_mm"] = round(random.uniform(1150, 1300), 1)

    elif scenario == "person_ahead":
        packet["ultrasonic_cm"] = round(random.uniform(220, 280), 1)
        packet["tof_mm"] = round(random.uniform(2300, 2700), 1)

    elif scenario == "car_approaching":
        packet["ultrasonic_cm"] = round(random.uniform(350, 450), 1)
        packet["tof_mm"] = round(random.uniform(3800, 4500), 1)
        # Rapid gyro change models the user's head/cane turning toward the noise.
        packet["gyro_z"] = round(random.uniform(15, 25), 2)

    elif scenario == "stairs_ahead":
        packet["ultrasonic_cm"] = round(random.uniform(90, 150), 1)
        packet["tof_mm"] = round(random.uniform(900, 1500), 1)
        packet["accel_z"] = round(random.uniform(1.5, 2.5), 3)  # cane tip drops

    elif scenario == "fall_detected":
        packet["accel_x"] = round(random.uniform(-8, 8), 2)
        packet["accel_y"] = round(random.uniform(-2, 2), 2)  # gravity axis disrupted
        packet["accel_z"] = round(random.uniform(-8, 8), 2)
        packet["gyro_x"] = round(random.uniform(-180, 180), 1)
        packet["gyro_y"] = round(random.uniform(-180, 180), 1)

    elif scenario == "sos_pressed":
        packet["sos_pressed"] = True

    elif scenario == "low_battery":
        state.battery_percent = max(2.0, state.battery_percent - 1.5)
        packet["battery_percent"] = round(state.battery_percent, 1)

    return packet


def run(
    backend_url: str,
    token: str,
    scenario: str,
    count: int,
    interval_seconds: float,
) -> None:
    state = SimulatorState()
    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(base_url=backend_url, timeout=5.0) as client:
        for i in range(count):
            active_scenario = random.choice(SCENARIOS) if scenario == "random" else scenario
            packet = generate_packet(active_scenario, state)

            try:
                response = client.post("/sensors/data", json=packet, headers=headers)
                status = "OK" if response.status_code == 201 else f"FAIL({response.status_code})"
            except httpx.RequestError as exc:
                status = f"ERROR({exc})"

            print(f"[{i + 1}/{count}] scenario={active_scenario:<16} -> {status} | {packet}")
            state.tick += 1
            time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="ECHO-CANE sensor simulator")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--token", required=True, help="Access token from /auth/login or /auth/register")
    parser.add_argument("--scenario", default="random", choices=SCENARIOS + ["random"])
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between packets")
    args = parser.parse_args()

    run(args.backend_url, args.token, args.scenario, args.count, args.interval)


if __name__ == "__main__":
    main()
