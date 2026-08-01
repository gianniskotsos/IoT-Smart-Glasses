#!/usr/bin/env python3
import json
import os
import random
import time

import paho.mqtt.client as mqtt_client

# MQTT broker settings
BROKER = os.getenv("BROKER_IP", "localhost")
PORT = int(os.getenv("BROKER_PORT", "1883"))
CLIENT_ID = "team08_2025_postc" + str(random.random())

TOPICS = [
    ("team08_2025/glasses/uplink/+", 0),
]


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
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)

        entity = data["data"][0]
        entity_id = entity["id"]

        incoming_topic = msg.topic

        parts = incoming_topic.split("/")

        new_topic = f"{parts[0]}/{parts[1]}/{entity_id}/{parts[2]}/{parts[3]}"
        if "alert" in parts[3]:
            client.publish(new_topic, payload, qos=1)
        else:
            client.publish(new_topic, payload)

        print("[REPUBLISH]")
        print(f"  IN : {incoming_topic}")
        print(f"  OUT: {new_topic} at {time.ctime()}")

    except Exception as e:
        print("[ERROR]", e)


def run():
    client = connect_mqtt()
    client.on_message = on_message
    client.loop_forever()


if __name__ == "__main__":
    run()
