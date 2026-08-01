#!/usr/bin/env python3
import io
import json
import os
import signal
import socket
import struct
import time

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

SERVER_HOST = os.getenv("VMS_IP", "localhost")
SERVER_PORT = int(os.getenv("VMS_INGESTION_PORT", "7091"))

FRAME_SIZE = (1296, 972)
JPEG_QUALITY = 99
CONNECT_RETRY_DELAY = 3.0

running = True


def get_device_id():
    config_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "config.json"
    )
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
            return cfg.get("device_id", f"namglasses-{os.uname().nodename}")
    except Exception:
        return f"namglasses-{os.uname().nodename}"


def handle_signal(signum, frame):
    global running
    running = False
    print("Signal received, stopping...", flush=True)


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


class SocketOutput(io.BufferedIOBase):
    """
    BufferedIOBase subclass for Picamera2's FileOutput.

    Each write(buf) call is one complete JPEG frame.
    We prefix it with a 4-byte big-endian length and send via TCP.
    """

    def __init__(self, host, port, stream_id):
        super().__init__()
        self.host = host
        self.port = port
        self.stream_id = stream_id
        self.sock = None
        self._connect()

    def _connect(self):
        while running and self.sock is None:
            try:
                print(f"Connecting to {self.host}:{self.port} ...", flush=True)
                s = socket.create_connection((self.host, self.port), timeout=10)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.sock = s
                id_bytes = self.stream_id.encode("utf-8")
                s.sendall(struct.pack(">I", len(id_bytes)))
                s.sendall(id_bytes)

                self.sock = s
                print(f"Connected as '{self.stream_id}'", flush=True)
            except OSError as e:
                print(
                    f"Connection failed: {e}. Retrying in {CONNECT_RETRY_DELAY}s...",
                    flush=True,
                )
                time.sleep(CONNECT_RETRY_DELAY)

    def writable(self):
        return True

    def write(self, buf):
        if not running:
            return 0

        if self.sock is None:
            self._connect()
            if self.sock is None:
                return 0

        if isinstance(buf, memoryview):
            buf = buf.tobytes()
        elif not isinstance(buf, (bytes, bytearray)):
            buf = bytes(buf)

        try:
            header = struct.pack(">I", len(buf))
            self.sock.sendall(header + buf)
            return len(buf)
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionAbortedError,
            OSError,
        ) as e:
            print(f"Socket error: {e}. Closing and will reconnect...", flush=True)
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
            return 0

    def flush(self):
        pass

    def close(self):
        try:
            if self.sock is not None:
                self.sock.close()
        except OSError:
            pass
        self.sock = None
        super().close()


def main():
    global running
    STREAM_ID = get_device_id()
    print(f"Starting streamer with ID: {STREAM_ID}")
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": FRAME_SIZE})
    picam2.configure(video_config)
    picam2.options["quality"] = JPEG_QUALITY

    sock_output = SocketOutput(SERVER_HOST, SERVER_PORT, STREAM_ID)
    encoder = JpegEncoder()
    file_output = FileOutput(sock_output)

    print("Starting camera recording...", flush=True)
    picam2.start_recording(encoder, file_output)

    try:
        while running:
            time.sleep(1.0)
    finally:
        print("Stopping camera recording.", flush=True)
        try:
            picam2.stop_recording()
        except Exception as e:
            print(f"Error stopping recording: {e}", flush=True)
        sock_output.close()
        print("Shutdown  complete.", flush=True)


if __name__ == "__main__":
    main()
