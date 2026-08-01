#!/usr/bin/env python3
import json
import os
import random
import threading
import time

import paho.mqtt.client as mqtt_client
import requests
from fall_detector.detect import detect_fall
from fall_detector.state import init_user_state
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.domain.write_precision import WritePrecision

influxdb_url = os.getenv("INFLUXDB_URL")
bucket = os.getenv("INFLUXDB_BUCKET")
org = os.getenv("INFLUXDB_ORG")
token = os.getenv("INFLUXDB_TOKEN")
location_measurement = "location_data"
status_measurement = "device_status"
heart_rate_measurement = "heart_rate_data"
# MQTT broker settings
BROKER = os.getenv("BROKER_IP")
PORT = int(os.getenv("BROKER_PORT"))
CLIENT_ID = "team08_2025_" + str(random.random())


client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api()
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


def handle_steps(device_id, payload, client):
    try:
        data = json.loads(payload)
        steps = int(data.get("steps", 0))
    except Exception:
        return

    print(f"[STEPS] {device_id}: {steps}")
    update_entity(device_id, {"steps": steps})


def handle_health(device_id, payload, client):
    try:
        data = json.loads(payload)
        hr = int(data.get("heart_rate", 0))
        timestamp = data.get("timestamp", None)
    except Exception:
        return
    write_api.write(
        bucket=bucket,
        org=org,
        record=Point(heart_rate_measurement)
        .tag("device_id", device_id)
        .field("heart_rate", hr)
        .time(time.time_ns(), WritePrecision.NS),
    )
    print(f"[HEALTH] {device_id}: HR={hr}")
    update_entity(device_id, {"heartRate": hr})
    r = requests.get(f"{ORION_URL}/{device_id}", headers=FIWARE_GET_HEADERS)
    entity = r.json()

    if hr > 120:
        print(f"ALERT: High heart rate ({hr}) on {device_id}")
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_highHeartRate",
            active=True,
            value=hr,
            ts=timestamp,
        )
    elif hr <= 100:
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_highHeartRate",
            active=False,
            value=hr,
            ts=timestamp,
        )


users = {}


def handle_fall_detect(device_id, payload, client):
    data = json.loads(payload)
    user_id = device_id

    if user_id not in users:
        users[user_id] = init_user_state()

    user_state = users[user_id]
    user_state["window"].append(data)

    if detect_fall(user_state, data):
        print(f"FALL detected for {user_id}")
        user_state["last_fall_ts"] = time.time()
        update_entity(
            user_id,
            {
                "alert_fall": {
                    "value": {
                        "ts": user_state["last_fall_ts"],
                    }
                }
            },
        )
        user_state["state"] = "NORMAL"


def handle_gps(device_id, payload, client):
    try:
        data = json.loads(payload)
        lat = data["lat"]
        lng = data["lng"]
        speed = data["speed"]
    except Exception:
        return
    point = (
        Point(location_measurement)
        .tag("device_id", device_id)
        .field("latitude", data["lat"])
        .field("longitude", data["lng"])
        .time(time.time_ns(), WritePrecision.NS)
    )  # speed goes to mqtt
    write_api.write(
        bucket=bucket,
        org=org,
        record=point,
    )
    print(f"[GPS] {device_id}: {lat},{lng}")
    update_entity(
        device_id,
        {"location": {"type": "Point", "coordinates": [lng, lat]}, "speed": speed},
    )


CYCLE_SEC = 2 * 60 * 60


def battery_from_uptime(uptime_sec):

    cycle_time = uptime_sec % CYCLE_SEC
    ratio = cycle_time / CYCLE_SEC
    battery = 100 * (1 - ratio)
    return int(battery)


def update_alert_if_changed(device_id, entity, alert_name, active, value, ts):
    current_active = entity.get(alert_name, {}).get("value", {}).get("active", False)

    print(f"Current active for {alert_name} on {device_id}: {current_active}")

    print(
        f"Comparing {alert_name} on {device_id}: "
        f"current_active={current_active}, new_active={active}"
    )

    if current_active == active:
        return

    print(f"[ALERT] {alert_name} → {'ACTIVE' if active else 'CLEARED'}")

    payload = {
        alert_name: {
            "type": "StructuredValue",
            "value": {"active": active, "value": value, "ts": ts},
        }
    }

    requests.patch(
        f"{ORION_URL}/{device_id}/attrs", headers=FIWARE_HEADERS, json=payload
    )


def check_status(device_id, cpu_val, mem_val, temp_val, battery_val, timestamp, entity):
    if cpu_val > 90:
        print(f"ALERT: High CPU usage ({cpu_val}%) on {device_id}")
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_cpu",
            active=True,
            value=cpu_val,
            ts=timestamp,
        )
    elif cpu_val < 70:
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_cpu",
            active=False,
            value=cpu_val,
            ts=timestamp,
        )
    if mem_val > 90:
        print(f"ALERT: High Memory usage ({mem_val}%) on {device_id}")
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_memory",
            active=True,
            value=mem_val,
            ts=timestamp,
        )
    elif mem_val < 70:
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_memory",
            active=False,
            value=mem_val,
            ts=timestamp,
        )

    if temp_val > 85:
        print(f"ALERT: High Temperature ({temp_val}°C) on {device_id}")
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_temperature",
            active=True,
            value=temp_val,
            ts=timestamp,
        )
    elif temp_val < 75:
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_temperature",
            active=False,
            value=temp_val,
            ts=timestamp,
        )

    if battery_val < 20:
        print(f"ALERT: Low Battery ({battery_val}%) on {device_id}")
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_battery",
            active=True,
            value=battery_val,
            ts=timestamp,
        )
    elif battery_val > 25:
        update_alert_if_changed(
            device_id,
            entity=entity,
            alert_name="alert_battery",
            active=False,
            value=battery_val,
            ts=timestamp,
        )


def write_status_to_influx(device_id, status):
    point = (
        Point(status_measurement)
        .tag("device_id", device_id)
        .field("cpu", status["cpu_percent"])
        .field("battery", status["battery"])
        .field("memory", status["mem_percent"])
        .field("temperature", status["temp_c"])
        .time(time.time_ns(), WritePrecision.NS)
    )
    write_api.write(bucket=bucket, org=org, record=point)


def handle_status(device_id, payload, client):
    data = {}
    try:
        data = json.loads(payload)

        if data.get("type") != "status":
            print(
                f" Received non-status data in status handler for {device_id},passing"
            )
            return
    except Exception:
        print(f"Failed to parse status payload for {device_id}: {payload}")
        return
    cpu_val = data.get("cpu_percent", 0)
    mem_val = data.get("mem_percent", 0)
    temp_val = data.get("temp_c", 0)
    uptime_val = data.get("uptime_sec", 0)
    timestamp = data.get("ts", None)
    battery_val = battery_from_uptime(uptime_val)
    status_value = {
        "battery": battery_val,
        "cpu_percent": cpu_val,
        "mem_percent": mem_val,
        "temp_c": temp_val,
        "loadavg": data.get("loadavg"),
        "uptime_sec": uptime_val,
        "ts": timestamp,
    }
    update_entity(device_id, {"status": status_value})
    r = requests.get(f"{ORION_URL}/{device_id}", headers=FIWARE_GET_HEADERS)

    if r.status_code != 200:
        print("Entity not found")
        return

    entity = r.json()
    check_status(device_id, cpu_val, mem_val, temp_val, battery_val, timestamp, entity)
    write_status_to_influx(device_id, status_value)


# MQTT DISPATCH

HANDLERS = {
    "heart_rate": handle_health,
    "location": handle_gps,
    "status": handle_status,
    "fall_detect_sensor": handle_fall_detect,
}


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            client.subscribe(TOPICS)
        else:
            print(f"Failed to connect, rc={rc}")

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client


def on_message(client, userdata, msg):
    topic_parts = msg.topic.split("/")
    device_id = topic_parts[2]
    suffix = topic_parts[-1]
    payload = msg.payload.decode()

    handler = HANDLERS.get(suffix)
    if handler:
        try:
            threading.Thread(
                target=handler, args=(device_id, payload, client), daemon=True
            ).start()
        except Exception as e:
            print(f"Error in handler {suffix} for {device_id}: {e}")
    else:
        print(f"No handler for topic: {suffix}")


def run():
    client = connect_mqtt()
    client.on_message = on_message
    client.loop_forever()


if __name__ == "__main__":
    run()
