import json
import os
import random
import time

import paho.mqtt.client as mqtt
from namglasses_sdk import NamGlassesSDK

BROKER = os.getenv("BROKER_IP", "localhost")
CLOUD_BROKER = os.getenv("BROKER_IP", "localhost")
PORT = int(os.getenv("BROKER_PORT", "1883"))
CLOUD_PORT = int(os.getenv("BROKER_PORT", "1883"))
SUB_TOPIC = "team08_2025/glasses/+/AI/responses"
SUB_TOPIC2 = "team08_2025/glasses/+/downlink/communication"
CLIENT_ID = f"team08_2025_messenger_{random.randint(1000, 9999)}"

sdk_dict = {}


def get_sdk(device_id):
    if device_id not in sdk_dict:
        print(f"[*] Initializing new SDK instance for device: {device_id}")
        sdk_dict[device_id] = NamGlassesSDK(
            device_id=device_id, broker=BROKER, port=PORT, qos=1
        )
    return sdk_dict[device_id]


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)

        text = data.get("message", str(data))

        topic_parts = msg.topic.split("/")
        device_id = topic_parts[2]

        print(f"[AI] Answer for {device_id}: {text}")

        sdk = get_sdk(device_id)
        sdk.display_text(text, duration_sec=10.0)
    except Exception as e:
        print(f"[!] Error processing message: {e}")


def main():
    print(f"Connecting to Cloud Broker ({CLOUD_BROKER})...")

    upstream_client = mqtt.Client(CLIENT_ID)
    upstream_client.on_message = on_message

    try:
        upstream_client.connect(CLOUD_BROKER, CLOUD_PORT)
        upstream_client.subscribe(SUB_TOPIC, qos=1)
        upstream_client.subscribe(SUB_TOPIC2, qos=1)
        upstream_client.loop_start()
        print(f"Listening for AI responses on: {SUB_TOPIC}")
        print(f"Listening for downlink communication on: {SUB_TOPIC2}")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
        for dev_id, sdk in sdk_dict.items():
            print(f"Disconnecting SDK for {dev_id}...")
            sdk.client.disconnect()
        upstream_client.loop_stop()
        upstream_client.disconnect()


if __name__ == "__main__":
    main()
