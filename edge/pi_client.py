#!/usr/bin/env python3
import base64
import datetime as dt
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import threading
import time
import uuid
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)
# --- Optional OLED (luma) imports (guarded) ---
OLED_AVAILABLE = False
try:
    from luma.core.interface.serial import spi
    from luma.core.render import canvas
    from luma.oled.device import ssd1309

    OLED_AVAILABLE = True
except Exception:
    OLED_AVAILABLE = False

# --- Optional Picamera2 support (guarded) ---
PICAMERA2_AVAILABLE = False
try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False

APP_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
RUN_EVENT = threading.Event()
RUN_EVENT.set()


def load_config(path: str) -> dict[str, Any]:
    with open(path, "r") as f:
        cfg = json.load(f)
    node_name = platform.node()  
    cfg.setdefault("device_id", f"namglasses-{node_name}")
    device_id = cfg["device_id"]
    cfg.setdefault("mqtt", {})
    m = cfg["mqtt"]
    m.setdefault("broker", os.getenv("BROKER_IP"))
    m.setdefault("port", int(os.getenv("BROKER_PORT", "1883")))
    m.setdefault("username", None)
    m.setdefault("password", None)
    m.setdefault("client_id", cfg["device_id"])
    m.setdefault("keepalive", 60)
    m.setdefault("clean_session", True)
    m.setdefault("qos", 1)
    m.setdefault("retain", False)
    m.setdefault("downlink_topic", f"team08_2025/glasses/{device_id}/downlink")
    m.setdefault("uplink_topic", f"team08_2025/glasses/{device_id}/status")
    m.setdefault("tls", False)

    cfg.setdefault("status", {})
    cfg["status"].setdefault("interval_sec", 30)

    cfg.setdefault("oled", {})
    o = cfg["oled"]
    o.setdefault("enabled", False)
    o.setdefault(
        "spi",
        {
            "port": 0,
            "device": 0,
            "gpio_DC": 25,
            "gpio_RST": 24,
            "bus_speed_hz": 8_000_000,
        },
    )
    o.setdefault("width", 128)
    o.setdefault("height", 64)
    o.setdefault("contrast", 255)

    cfg.setdefault("camera", {})
    c = cfg["camera"]
    c.setdefault("method", "auto")  # "auto" | "picamera2" | "libcamera"
    c.setdefault("resolution", [1280, 720])
    c.setdefault("format", "jpeg")
    return cfg


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_cpu_temp_c() -> float | None:
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return int(f.read().strip()) / 1000.0
    except Exception:
        return None


def read_uptime_sec() -> float | None:
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])
    except Exception:
        return None


def read_loadavg() -> tuple[float, float, float]:
    try:
        return os.getloadavg()
    except Exception:
        return (0.0, 0.0, 0.0)


def read_mem_percent() -> float | None:
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                k, v = line.split(":")
                meminfo[k] = int(v.strip().split()[0])  # kB
        total = meminfo["MemTotal"]
        avail = meminfo.get("MemAvailable", meminfo["MemFree"])
        used_ratio = 1.0 - (avail / total)
        return round(used_ratio * 100.0, 2)
    except Exception:
        return None


def cpu_percent(interval: float = 0.1) -> float | None:
    def read():
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("cpu "):
                    parts = [float(x) for x in line.split()[1:]]
                    idle = parts[3] + parts[4]
                    total = sum(parts)
                    return idle, total
        return None, None

    try:
        idle1, total1 = read()
        if idle1 is None:
            return None
        time.sleep(interval)
        idle2, total2 = read()
        if idle2 is None:
            return None
        didle = idle2 - idle1
        dtotal = total2 - total1
        if dtotal <= 0:
            return None
        usage = (1.0 - didle / dtotal) * 100.0
        return round(usage, 2)
    except Exception:
        return None


# --- OLED helpers ---
class Oled:
    def __init__(self, cfg: dict[str, Any]):
        self.enabled = cfg.get("enabled", False) and OLED_AVAILABLE
        self.device = None
        if self.enabled:
            s = cfg["spi"]
            serial = spi(
                port=s["port"],
                device=s["device"],
                gpio_DC=s["gpio_DC"],
                gpio_RST=s["gpio_RST"],
                bus_speed_hz=s["bus_speed_hz"],
            )
            self.device = ssd1309(serial, width=cfg["width"], height=cfg["height"])
            self.device.contrast(cfg.get("contrast", 255))

    def display_text(
        self,
        text: str,
        x: int = 0,
        y: int = 0,
        clear: bool = True,
        duration_sec: float | None = None,
    ):
        print(f"OLED Display: {text}", flush=True)

        if not self.enabled or self.device is None:
            return

        with canvas(self.device) as draw:
            if clear:
                # clear screen if needed
                pass
            draw.multiline_text((x, y), text, fill=255, spacing=2)

        if duration_sec and duration_sec > 0:
            time.sleep(duration_sec)


# --- Camera helpers ---
class Camera:
    def __init__(self, cfg: dict[str, Any]):
        self.method = cfg.get("method", "auto")
        self.resolution = tuple(cfg.get("resolution", [1280, 720]))
        self.format = cfg.get("format", "jpeg")

    def _capture_picamera2(self) -> bytes | None:
        if not PICAMERA2_AVAILABLE:
            return None
        try:
            picam2 = Picamera2()
            cfg = picam2.create_still_configuration(main={"size": self.resolution})
            picam2.configure(cfg)
            picam2.start()
            time.sleep(0.2)
            b = picam2.capture_array("main")
            import io

            from PIL import Image

            img = Image.fromarray(b)
            bio = io.BytesIO()
            img.save(bio, format="JPEG")
            picam2.close()
            return bio.getvalue()
        except Exception:
            try:
                picam2.close()
            except Exception:
                pass
            return None

    def _capture_libcamera(self) -> bytes | None:
        cmd = [
            "libcamera-still",
            "-n",
            "--width",
            str(self.resolution[0]),
            "--height",
            str(self.resolution[1]),
            "-o",
            "-",
        ]
        try:
            out = subprocess.run(cmd, check=True, capture_output=True)
            return out.stdout
        except Exception:
            return None

    def capture(self) -> bytes | None:
        if self.method == "picamera2":
            return self._capture_picamera2()
        if self.method == "libcamera":
            return self._capture_libcamera()
        data = self._capture_picamera2()
        if data:
            return data
        return self._capture_libcamera()


# --- MQTT client wrapper for the glasses ---
class GlassesClient:
    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg
        self.mqtt_cfg = cfg["mqtt"]
        self.status_cfg = cfg["status"]
        self.device_id = cfg["device_id"]

        self.oled = Oled(cfg["oled"])
        self.camera = Camera(cfg["camera"])

        self.client = mqtt.Client(
            client_id=self.mqtt_cfg["client_id"],
            clean_session=self.mqtt_cfg.get("clean_session", True),
        )
        if self.mqtt_cfg.get("username"):
            self.client.username_pw_set(
                self.mqtt_cfg["username"], self.mqtt_cfg.get("password")
            )
        if self.mqtt_cfg.get("tls"):
            self.client.tls_set()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.reload_requested = False
        self.qos = int(self.mqtt_cfg.get("qos", 1))
        self.retain = bool(self.mqtt_cfg.get("retain", False))
        self.downlink = self.mqtt_cfg["downlink_topic"]
        self.uplink = self.mqtt_cfg["uplink_topic"]

        self.status_thread = threading.Thread(target=self._status_loop, daemon=True)

    def connect(self):
        self.client.connect(
            self.mqtt_cfg["broker"],
            int(self.mqtt_cfg["port"]),
            int(self.mqtt_cfg["keepalive"]),
        )
        self.client.loop_start()
        self.status_thread.start()

    def disconnect(self):
        try:
            self.client.loop_stop()
        except Exception:
            pass
        try:
            self.client.disconnect()
        except Exception:
            pass

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected with result code {rc}")
        client.subscribe(self.downlink, qos=self.qos)
        print(f"Subscribed to downlink topic: {self.downlink}")
        self.publish_json(
            {
                "type": "hello",
                "device_id": self.device_id,
                "ts": iso_now(),
                "capabilities": [
                    "display_text",
                    "take_photo",
                    "status",
                    "set_config",
                    "reload",
                    "ping",
                ],
            }
        )

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected (rc={rc})")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
        except Exception as e:
            logger.error(f"Bad JSON on {msg.topic}: {e}")
            return

        cmd = data.get("cmd")
        req_id = data.get("request_id") or str(uuid.uuid4())
        args = data.get("args", {}) or {}
        if not cmd:
            self.publish_error(req_id, cmd, "missing 'cmd'")
            return

        try:
            if cmd == "display_text":
                text = str(args.get("text", ""))
                x = int(args.get("x", 0))
                y = int(args.get("y", 0))
                clear = bool(args.get("clear", True))
                duration = args.get("duration_sec")
                self.oled.display_text(
                    text, x=x, y=y, clear=clear, duration_sec=duration
                )
                self.publish_ack(req_id, cmd)

            elif cmd == "take_photo":
                img = self.camera.capture()
                if not img:
                    self.publish_error(req_id, cmd, "capture failed")
                    return
                b64 = base64.b64encode(img).decode("ascii")
                self.publish_json(
                    {
                        "type": "photo",
                        "request_id": req_id,
                        "device_id": self.device_id,
                        "ts": iso_now(),
                        "mime": "image/jpeg",
                        "encoding": "base64",
                        "data": b64,
                    }
                )

            elif cmd == "status":
                self.publish_status(req_id=req_id)
                self.publish_ack(req_id, cmd)

            elif cmd == "set_config":
                patch = args.get("patch", {})
                ok, changed = self.apply_config_patch(patch)
                if ok:
                    self.publish_ack(req_id, cmd, extra={"changed_keys": changed})
                else:
                    self.publish_error(req_id, cmd, "invalid patch")

            elif cmd == "reload":
                self.publish_ack(req_id, cmd)
                self.reload_requested = True

            elif cmd == "ping":
                self.publish_json(
                    {
                        "type": "pong",
                        "request_id": req_id,
                        "device_id": self.device_id,
                        "ts": iso_now(),
                    }
                )

            else:
                self.publish_error(req_id, cmd, f"unknown command '{cmd}'")

        except Exception as e:
            logger.exception("Command handling failed")
            self.publish_error(req_id, cmd, str(e))

    def publish_json(self, obj: dict[str, Any]):
        payload = json.dumps(obj, separators=(",", ":"))
        self.client.publish(self.uplink, payload, qos=self.qos, retain=self.retain)

    def publish_ack(
        self, request_id: str, cmd: str, extra: dict[str, Any] | None = None
    ):
        obj = {
            "type": "ack",
            "request_id": request_id,
            "cmd": cmd,
            "device_id": self.device_id,
            "ts": iso_now(),
            "ok": True,
        }
        if extra:
            obj.update(extra)
        self.publish_json(obj)

    def publish_error(self, request_id: str, cmd: str | None, error: str):
        self.publish_json(
            {
                "type": "error",
                "request_id": request_id,
                "cmd": cmd,
                "device_id": self.device_id,
                "ts": iso_now(),
                "error": error,
            }
        )

    def publish_status(self, req_id: str | None = None):
        obj = {
            "type": "status",
            "request_id": req_id,
            "device_id": self.device_id,
            "ts": iso_now(),
            "cpu_percent": cpu_percent(0.12),
            "mem_percent": read_mem_percent(),
            "temp_c": read_cpu_temp_c(),
            "loadavg": read_loadavg(),
            "uptime_sec": read_uptime_sec(),
        }
        self.publish_json(obj)

    def _status_loop(self):
        interval = int(self.status_cfg.get("interval_sec", 30))
        while RUN_EVENT.is_set():
            self.publish_status(req_id=None)
            for _ in range(interval):
                if not RUN_EVENT.is_set():
                    break
                time.sleep(1)

    def apply_config_patch(self, patch: dict[str, Any]) -> tuple[bool, list]:
        if not isinstance(patch, dict):
            return False, []
        cur = load_config(CONFIG_PATH)
        changed = []

        def merge(d, p, path=""):
            nonlocal changed
            for k, v in p.items():
                if isinstance(v, dict) and isinstance(d.get(k), dict):
                    merge(d[k], v, path + k + ".")
                else:
                    if d.get(k) != v:
                        d[k] = v
                        changed.append(path + k)

        merge(cur, patch)
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cur, f, indent=2)
        os.replace(tmp, CONFIG_PATH)

        mqtt_keys = (
            "broker",
            "port",
            "username",
            "password",
            "client_id",
            "qos",
            "retain",
            "downlink_topic",
            "uplink_topic",
            "tls",
            "keepalive",
            "clean_session",
        )
        if any(("mqtt." + k) in changed for k in mqtt_keys):
            self.reload_requested = True
        return True, changed


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    def handle_sigterm(signum, frame):
        RUN_EVENT.clear()

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    while RUN_EVENT.is_set():
        cfg = load_config(CONFIG_PATH)
        print(f"Starting NamGlasses client '{cfg['device_id']}'...", flush=True)
        client = GlassesClient(cfg)
        client.connect()
        try:
            while RUN_EVENT.is_set() and not client.reload_requested:
                time.sleep(0.5)
        finally:
            client.disconnect()
        if not RUN_EVENT.is_set():
            break
        time.sleep(1.0)


if __name__ == "__main__":
    sys.exit(main())
