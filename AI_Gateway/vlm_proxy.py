import base64
import json
import os
import random
import threading

import paho.mqtt.client as mqtt_client
import requests

# MQTT / broker settings
BROKER = os.getenv("BROKER_IP")
PORT = int(os.getenv("BROKER_PORT"))
CLIENT_ID = "team08_2025_VLM_" + str(random.random())


# VLM API settings
API_URL = os.getenv("VLM_API_URL")
API_KEY = os.getenv("VLM_API_KEY")
MODEL_NAME = os.getenv("VLM_MODEL_NAME")

SNAPSHOT_BASE = os.getenv("VMS_IP") + ":" + str(os.getenv("VMS_PORT"))


def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}\n")

    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.connect(BROKER, PORT)
    return client


def publish_response(client: mqtt_client.Client, device_id: str, message: str):
    topic = f"team08_2025/glasses/{device_id}/AI/responses"
    print(f"Publishing to {topic}: {message}")
    client.publish(topic, message, qos=1)


def encode_image_to_base64(url: str) -> str:
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    return base64.b64encode(r.content).decode("utf-8")


def run_vlm_and_publish(
    mqtt_client_obj: mqtt_client.Client, device_id: str, prompt: str
):
    try:
        print(f"Running VLM for device {device_id} prompt: {prompt}")
        snapshot_url = f"http://{SNAPSHOT_BASE}/{device_id}/snapshot.jpg"
        image_b64 = encode_image_to_base64(snapshot_url)

        vlm_prompt = f"""You are a vision-language assistant.
Your job:
1. Answer the user's question ONLY using information directly visible in the image, answer only taking context ONLY from the picture.
2. Do not hallucinate objects, text, or details that are not clearly visible.
3. Keep answers short and direct (1-2 sentences max).
4. try to help with navigation based on visible surroundings.
5. if there is safery concern, mention it in your answer.
6. Answer in the language of the user's question.
The user's question is: {prompt}?"""

        payload = {
            "model": MODEL_NAME,
            "prompt": vlm_prompt,
            "image": image_b64,
        }

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
        }

        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if not resp.ok:
            print("VLM request failed", resp.status_code, resp.text)
            resp.raise_for_status()

        data = resp.json()
        output = json.dumps({"message": data.get("output") or data}, ensure_ascii=False)
        # publish only to allowed responses topic
        publish_response(mqtt_client_obj, device_id, output)

    except Exception as e:
        err_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
        print("Error during VLM processing:", e)
        try:
            publish_response(mqtt_client_obj, device_id, err_msg)
        except Exception:
            print("Failed to publish error message")


def subscribe_and_listen(client: mqtt_client.Client):
    topics = [("team08_2025/glasses/+/AI/queries", 0)]
    client.subscribe(topics)

    def on_message(client_obj, userdata, msg):
        payload = msg.payload.decode("utf-8")
        print(f"Received `{payload}` from `{msg.topic}` topic")
        topic_parts = msg.topic.split("/")
        if len(topic_parts) >= 3:
            device_id = topic_parts[2]
        else:
            return

        if msg.topic.endswith("/AI/queries"):
            threading.Thread(
                target=run_vlm_and_publish,
                args=(client, device_id, payload),
                daemon=True,
            ).start()

    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe_and_listen(client)
    client.loop_forever()


if __name__ == "__main__":
    run()
