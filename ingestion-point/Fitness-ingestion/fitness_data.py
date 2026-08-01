import os
import random
import time
from datetime import datetime

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from influxdb_client import InfluxDBClient, Point, WritePrecision

BROKER = os.getenv("BROKER_IP")
PORT = int(os.getenv("BROKER_PORT"))
CLIENT_ID = "team08_2025_" + str(random.random())


TOPICS = [
    ("team08_2025/glasses/+/heart_rate", 0),
    ("team08_2025/glasses/+/location", 0),
    ("team08_2025/glasses/+/status", 0),
    ("team08_2025/glasses/+/fall_detect_sensor", 0),
]

# =========================
# FIWARE ORION CONFIG
# =========================
ORION_URL = os.getenv("ORION_ENTITIES_URL")
FIWARE_SERVICE_PATH = "/team_08_2025__smartglasses"

FIWARE_HEADERS = {
    "Content-Type": "application/json",
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}
FIWARE_GET_HEADERS = {
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}


SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.oxygen_saturation.read",
]


def check_and_create_entity(entity_id):
    r = requests.get(f"{ORION_URL}/{entity_id}", headers=FIWARE_GET_HEADERS)

    if r.status_code == 404:
        print(f"[CHECK] Entity NOT FOUND → creating {entity_id}")

        payload = {
            "id": entity_id,
            "type": "SmartGlasses",
            "heartRate": {"type": "Number", "value": 0},
            "alert_highHeartRate": {
                "type": "StructuredValue",
                "value": {"active": False, "value": None, "ts": None},
            },
            "alert_lowOxygen": {
                "type": "StructuredValue",
                "value": {"active": False, "value": None, "ts": None},
            },
            "alert_fall": {"type": "StructuredValue", "value": {"ts": None}},
            "alert_cpu": {
                "type": "StructuredValue",
                "value": {"active": False, "value": None, "ts": None},
            },
            "alert_battery": {
                "type": "StructuredValue",
                "value": {"active": False, "value": None, "ts": None},
            },
            "alert_temperature": {
                "type": "StructuredValue",
                "value": {"active": False, "value": None, "ts": None},
            },
            "alert_memory": {
                "type": "StructuredValue",
                "value": {"active": False, "value": None, "ts": None},
            },
            "location": {
                "type": "geo:json",
                "value": {
                    "type": "Point",
                    "coordinates": [0.0, 0.0],  # [longitude, latitude]
                },
            },
            "speed": {"type": "Number", "value": 0},
            "status": {
                "type": "StructuredValue",
                "value": {
                    "battery": 0,
                    "cpu_percent": 0,
                    "mem_percent": 0,
                    "temp_c": 0,
                    "loadavg": [0, 0, 0],
                    "uptime_sec": 0,
                    "ts": "none",
                },
            },
            "oxygenSaturation": {"type": "Number", "value": 0},
        }

        cr = requests.post(ORION_URL, headers=FIWARE_HEADERS, json=payload)
        if cr.status_code == 201:
            print(f" Created entity {entity_id}")
        else:
            print(f" Failed to create entity: {cr.text}")

    else:
        print("[CHECK] Entity exists")


def update_entity(entity_id, attrs: dict):
    check_and_create_entity(entity_id)

    payload = {}

    for k, v in attrs.items():
        if isinstance(v, dict):
            payload[k] = {"type": "StructuredValue", "value": v}
        elif k == "location":
            payload[k] = {
                "type": "geo:json",
                "value": {"type": "Point", "coordinates": [v["lng"], v["lat"]]},
            }
        elif isinstance(v, (int, float)):
            payload[k] = {"type": "Number", "value": v}
        else:
            payload[k] = {"type": "Text", "value": v}

    r = requests.patch(
        f"{ORION_URL}/{entity_id}/attrs",
        headers=FIWARE_HEADERS,
        json=payload,
    )

    if r.status_code == 204:
        print(f" Updated {entity_id}: {attrs}")
    else:
        print(f" Update failed: {r.status_code} {r.text}")


influxdb_url = os.getenv("INFLUXDB_URL")

bucket = os.getenv("INFLUXDB_BUCKET")
org = os.getenv("INFLUXDB_ORG")
token = os.getenv("INFLUXDB_TOKEN")
measurement = "fitness_data"

client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api()
refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
device_id = "team08smartglasses1"

google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")


def get_fitness_service():
   
    creds = Credentials(
        token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=google_client_id,
        client_secret=google_client_secret,
        scopes=SCOPES,
    )

    return build("fitness", "v1", credentials=creds)


i = 0


# --- Helper to fetch datasets ---
def fetch_dataset(service, data_source_id):
    now = int(time.time() * 1_000_000_000)  # nanoseconds
    lookback = int((time.time() - (7 * 24 * 3600)) * 1_000_000_000)

    dataset_id = f"{lookback}-{now}"
    try:
        dataset = (
            service.users()
            .dataSources()
            .datasets()
            .get(userId="me", dataSourceId=data_source_id, datasetId=dataset_id)
            .execute()
        )
        return dataset.get("point", [])
    except Exception as e:
        print(f"Error fetching {data_source_id}: {e}")
        return []


# --- Main loop ---
print("Google Fit → InfluxDB started")

last_sent_spo2_ts = 0

while True:
    try:
        fitness_service = get_fitness_service()
        data_streams = {
            "steps": "derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas",
            "oxygen_saturation": "derived:com.google.oxygen_saturation:com.google.android.gms:merged",
        }

        total_points = 0

        for field_name, stream_id in data_streams.items():
            points = fetch_dataset(fitness_service, stream_id)

            if not points:
                print(f"No new data for {field_name}")
                continue

            
            for p in points:
                val1 = (
                    p["value"][0].get("fpVal")
                    if p["value"][0].get("fpVal") is not None
                    else p["value"][0].get("intVal")
                )
                ts = int(p["startTimeNanos"])

                point = (
                    Point(measurement)
                    .tag("device_id", device_id)
                    .field(field_name, val1)
                    .time(ts, WritePrecision.NS)
                )
                write_api.write(bucket=bucket, org=org, record=point)

            total_points += len(points)

            
            if field_name == "oxygen_saturation":
               
                latest_point = max(points, key=lambda p: int(p["startTimeNanos"]))

                val = latest_point["value"][0].get("fpVal")
                ts_nanos = int(latest_point["startTimeNanos"])
                ts_sec = ts_nanos / 1_000_000_000

       
                if ts_sec > last_sent_spo2_ts:
                    value_to_send = float(val)
                 
                    update_entity(device_id, {"oxygenSaturation": value_to_send})

                    last_sent_spo2_ts = ts_sec
                    readable_ts = datetime.fromtimestamp(ts_sec).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    print(
                        f"Successfully triggered Orion update for SpO2: {value_to_send} at {readable_ts}"
                    )
                else:
                    print(f"SpO2 value is old (ts: {ts_sec}), skipping Orion update.")

        print(f"[{datetime.now()}] Sync cycle complete. Total points: {total_points}")

    except Exception as e:
        print(f"Error in sync cycle: {e}")

    time.sleep(10)
