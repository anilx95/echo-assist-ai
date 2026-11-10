import httpx
import random
import time

BASE_URL = "http://127.0.0.1:8000"

DEVICE_ID = "ECHO_CANE_001"

DEMO_USER = {
    "full_name": "ECHO Cane Simulator",
    "email": "echo.cane.simulator@example.com",
    "password": "EchoAssist123",
    "preferred_language": "en"
}


def generate_sensor_packet():
    return {
        "device_id": DEVICE_ID,

        "ultrasonic_cm": round(random.uniform(40, 300), 2),
        "tof_mm": round(random.uniform(300, 2500), 2),

        "accel_x": round(random.uniform(-1.0, 1.0), 3),
        "accel_y": round(random.uniform(-1.0, 1.0), 3),
        "accel_z": round(random.uniform(9.2, 10.2), 3),

        "gyro_x": round(random.uniform(-5, 5), 3),
        "gyro_y": round(random.uniform(-5, 5), 3),
        "gyro_z": round(random.uniform(-5, 5), 3),

        "sos_pressed": False,

        "battery_percent": round(
            random.uniform(60, 100),
            1
        ),

        "timestamp": int(time.time() * 1000)
    }


def get_access_token():

    print("Connecting simulator to ECHO-ASSIST AI...")

    register_response = httpx.post(
        f"{BASE_URL}/auth/register",
        json=DEMO_USER,
        timeout=10
    )

    if register_response.status_code == 201:

        print("Simulator user registered.")

        return register_response.json()["access_token"]


    if register_response.status_code == 409:

        print("Simulator user already exists.")
        print("Logging in...")

        login_response = httpx.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": DEMO_USER["email"],
                "password": DEMO_USER["password"]
            },
            timeout=10
        )

        login_response.raise_for_status()

        print("Login successful.")

        return login_response.json()["access_token"]


    print("Registration failed:")
    print(register_response.text)

    register_response.raise_for_status()


def send_sensor_packet(token, packet):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = httpx.post(
        f"{BASE_URL}/sensors/data",
        json=packet,
        headers=headers,
        timeout=10
    )

    return response


def ensure_device_registered(token):
    response = httpx.post(
        f"{BASE_URL}/devices",
        json={
            "device_id": DEVICE_ID,
            "device_name": "ECHO-CANE Simulator",
            "is_simulator": True,
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if response.status_code not in (201, 409):
        response.raise_for_status()


def main():

    print("=" * 50)
    print("ECHO-ASSIST AI SMART CANE SIMULATOR")
    print("=" * 50)

    try:
        token = get_access_token()

    except Exception as error:

        print("\nCould not connect to backend.")
        print(error)
        return


    print("\nDevice:", DEVICE_ID)
    print("Backend:", BASE_URL)
    print("Status: CONNECTED")

    try:
        ensure_device_registered(token)
    except Exception as error:
        print("Could not register simulator device:", error)
        return
    print("\nSending sensor data...\n")


    while True:

        packet = generate_sensor_packet()

        try:

            response = send_sensor_packet(
                token,
                packet
            )

            if response.status_code == 201:

                saved = response.json()

                print(
                    f"[SAVED] "
                    f"ID={saved['id']} | "
                    f"Ultrasonic={packet['ultrasonic_cm']} cm | "
                    f"ToF={packet['tof_mm']} mm | "
                    f"Battery={packet['battery_percent']}%"
                )

            else:

                print(
                    "[ERROR]",
                    response.status_code,
                    response.text
                )


        except httpx.ConnectError:

            print(
                "[CONNECTION ERROR] "
                "Backend is not running."
            )


        except Exception as error:

            print(
                "[ERROR]",
                error
            )


        time.sleep(1)


if __name__ == "__main__":
    main()
