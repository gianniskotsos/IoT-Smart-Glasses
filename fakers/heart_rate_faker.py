import datetime as dt
import json
import os
import random
import time

import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("BROKER_IP", "localhost")
MQTT_PORT = int(os.getenv("BROKER_PORT", "1883"))

DEVICE_ID = os.getenv("DEVICE_ID")
TOPIC = f"team08_2025/glasses/{DEVICE_ID}/heart_rate"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to EMQX at {MQTT_BROKER}")
    else:
        print(f"Connection failed with code {rc}")


def new_target():
    return random.randint(60, 140)


current_hr = random.randint(65, 85)
target_hr = new_target()


client = mqtt.Client()



client.on_connect = on_connect

try:
    print(f"Connecting to {MQTT_BROKER}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    t = 1
    while True:
        t += 1
        heart_rate = round(current_hr)
        if t % 10 == 0:
            if abs(current_hr - target_hr) < 1:
                target_hr = new_target()

         
            direction = 1 if target_hr > current_hr else -1
            step_size = random.uniform(0.5, 1.5)

            current_hr += direction * step_size

            
            current_hr = max(60, min(130, current_hr))

            heart_rate = round(current_hr)
        else:
           
            if heart_rate > 122:
                heart_rate = round(current_hr - random.uniform(-0.5, 1.5))
            else:
                heart_rate = round(current_hr + random.uniform(-1, 1))
        payload = {
            "heart_rate": heart_rate,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        }

        json_payload = json.dumps(payload)

       
        result = client.publish(TOPIC, json_payload, qos=1)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published to {TOPIC}: {json_payload}")
        else:
            print(f"Failed to publish to {TOPIC}")

        time.sleep(5)

except KeyboardInterrupt:
    print("\nStopping Faker...")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"An error occurred: {e}")
