import os

import requests

ORION_URL = os.getenv("ORION_SUBSCRIPTION_URL")

FIWARE_SERVICE_PATH = "/team_08_2025__smartglasses"

HEADERS = {
    "Content-Type": "application/json",
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}


def create_subscription(payload):
    r = requests.post(ORION_URL, headers=HEADERS, json=payload)

    if r.status_code == 201:
        print(f"Created: {payload['description']}")
    elif r.status_code == 409:
        print(f" Already exists: {payload['description']}")
    else:
        print(f"Error ({r.status_code}): {r.text}")


#  HEART RATE
heart_rate_sub = {
    "description": "heart rate live",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["heartRate"]},
    },
    "notification": {
        "attrs": ["heartRate"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/heartRate",
        },
    },
}

#  SPEED
speed_sub = {
    "description": "speed live",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["speed"]},
    },
    "notification": {
        "attrs": ["speed"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/speed",
        },
    },
}

#  LOCATION
location_sub = {
    "description": "location live",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["location"]},
    },
    "notification": {
        "attrs": ["location"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/gps",
        },
    },
}

#  STATUS
status_sub = {
    "description": "status live",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["status"]},
    },
    "notification": {
        "attrs": ["status"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/state",
        },
    },
}

oxygen_sub = {
    "description": "oxygen saturation live",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["oxygenSaturation"]},
    },
    "notification": {
        "attrs": ["oxygenSaturation"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/oxygenSaturation",
        },
    },
}
alert_high_heart_rate_sub = {
    "description": "high heart rate alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_highHeartRate"]},
    },
    "notification": {
        "attrs": ["alert_highHeartRate"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_high_heart_rate",
        },
    },
}
alert_low_oxygen_sub = {
    "description": "low oxygen saturation alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_lowOxygen"]},
    },
    "notification": {
        "attrs": ["alert_lowOxygen"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_lowOxygen",
        },
    },
}
alert_memory_sub = {
    "description": "memory alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_memory"]},
    },
    "notification": {
        "attrs": ["alert_memory"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_memory",
        },
    },
}
alert_fall_sub = {
    "description": "fall alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_fall"]},
    },
    "notification": {
        "attrs": ["alert_fall"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_fall",
        },
    },
}
alert_battery_sub = {
    "description": "battery alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_battery"]},
    },
    "notification": {
        "attrs": ["alert_battery"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_battery",
        },
    },
}
alert_cpu_sub = {
    "description": "cpu alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_cpu"]},
    },
    "notification": {
        "attrs": ["alert_cpu"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_cpu",
        },
    },
}
alert_temperature_sub = {
    "description": "temperature alert",
    "subject": {
        "entities": [{"idPattern": ".*", "type": "SmartGlasses"}],
        "condition": {"attrs": ["alert_temperature"]},
    },
    "notification": {
        "attrs": ["alert_temperature"],
        "mqtt": {
            "url": f"mqtt://{os.getenv('BROKER_IP')}:{os.getenv('BROKER_PORT')}",
            "topic": "team08_2025/glasses/uplink/alert_temperature",
        },
    },
}
if __name__ == "__main__":
    subscriptions = [
        heart_rate_sub,
        speed_sub,
        location_sub,
        status_sub,
        oxygen_sub,
        alert_high_heart_rate_sub,
        alert_low_oxygen_sub,
        alert_memory_sub,
        alert_fall_sub,
        alert_battery_sub,
        alert_cpu_sub,
        alert_temperature_sub
    ]

    for sub in subscriptions:
        create_subscription(sub)
