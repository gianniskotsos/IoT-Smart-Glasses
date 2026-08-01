#!/usr/bin/env python3
import base64
import json
import logging
import os
import threading
import time
import uuid
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class NamGlassesSDK:
    def __init__(
        self,
        device_id: str,
        broker: str = os.getenv("BROKER_IP", "localhost"),
        port: int = int(os.getenv("BROKER_PORT", "1883")),
        username: str | None = None,
        password: str | None = None,
        client_id: str | None = None,
        keepalive: int = 60,
        clean_session: bool = True,
        qos: int = 1,
    ):
        self.device_id = device_id
        self.qos = qos

        
        self.downlink = f"team08_2025/glasses/{device_id}/downlink"
        self.uplink = f"team08_2025/glasses/{device_id}/uplink"

        self.client = mqtt.Client(
            client_id=client_id or f"sdk-{uuid.uuid4()}", clean_session=clean_session
        )

        if username:
            self.client.username_pw_set(username, password)

        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect  

        self.client.connect(broker, port, keepalive)
        self.client.loop_start()

        self._waiters: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
           
            client.subscribe(self.uplink, qos=self.qos)
            logger.info(f"SDK connected and subscribed to {self.uplink}")
        else:
            logger.error(f"SDK connection failed with code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        msg_device_id = data.get("device_id")
        if msg_device_id != self.device_id:
            return

        req_id = data.get("request_id")
        if not req_id:
            return
        with self._lock:
            if req_id in self._waiters:
                self._waiters[req_id]["payload"] = data
                self._waiters[req_id]["event"].set()

    def _send(
        self, cmd: str, args: dict[str, Any] | None = None, timeout: float = 10.0
    ) -> dict[str, Any]:
        req_id = str(uuid.uuid4())
        payload = {
            "cmd": cmd,
            "args": args or {},
            "request_id": req_id,
            "device_id": self.device_id,  
            "ts": time.time(),
        }

        evt = threading.Event()
        with self._lock:
            self._waiters[req_id] = {"event": evt, "payload": None}

        self.client.publish(self.downlink, json.dumps(payload), qos=self.qos)
        logger.info(
            f"Published command '{cmd}' to topic '{self.downlink}' with request_id '{req_id}'"
        )
        ok = evt.wait(timeout)
        with self._lock:
            waiter_data = self._waiters.pop(req_id, {"payload": None})
            resp = waiter_data["payload"]

        if not ok or resp is None:
            raise TimeoutError(
                f"No response from device '{self.device_id}' for command '{cmd}'"
            )

        if resp.get("type") == "error":
            raise RuntimeError(f"Device Error: {resp.get('error')}")

        return resp

    def display_text(
        self,
        text: str,
        duration_sec: float = 2.0,
        x: int = 0,
        y: int = 0,
        clear: bool = True,
    ):
        return self._send(
            "display_text",
            {
                "text": text,
                "duration_sec": duration_sec,
                "x": x,
                "y": y,
                "clear": clear,
            },
        )

    def take_photo(self, timeout: float = 20.0) -> bytes:
        req_id = str(uuid.uuid4())
        payload = {
            "cmd": "take_photo",
            "args": {},
            "request_id": req_id,
            "device_id": self.device_id,
        }

        evt = threading.Event()
        with self._lock:
            self._waiters[req_id] = {"event": evt, "payload": None}

        self.client.publish(self.downlink, json.dumps(payload), qos=self.qos)

        if not evt.wait(timeout):
            with self._lock:
                self._waiters.pop(req_id, None)
            raise TimeoutError(f"Timed out waiting for photo from {self.device_id}")

        with self._lock:
            resp = self._waiters.pop(req_id)["payload"]

        if not resp or resp.get("type") != "photo":
            raise RuntimeError("Unexpected response type")

        if resp.get("encoding") == "base64":
            return base64.b64decode(resp["data"])
        raise RuntimeError("Unsupported encoding")

    def get_status(self, timeout: float = 10.0) -> dict[str, Any]:
        resp = self._send("status", timeout=timeout)
        return resp

    def set_config(self, patch: dict[str, Any], timeout: float = 10.0):
        return self._send("set_config", {"patch": patch}, timeout=timeout)

    def reload(self, timeout: float = 10.0):
        return self._send("reload", {}, timeout=timeout)

    def ping(self, timeout: float = 5.0) -> dict[str, Any]:
        return self._send("ping", {}, timeout=timeout)
