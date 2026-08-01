import socket
import struct
import threading
import time
from io import BytesIO

from flask import Flask, Response, abort, send_file

LISTEN_HOST = "0.0.0.0"
INGEST_PORT = 7091
HTTP_PORT = 7090


all_streams = {}
streams_lock = threading.Lock()

app = Flask(__name__)


def receiver_thread():
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((LISTEN_HOST, INGEST_PORT))
        server_sock.listen(10)
        print(f"Cloud Ingest Server on port {INGEST_PORT}")

        while True:
            conn, addr = server_sock.accept()
            client_thread = threading.Thread(target=handle_camera, args=(conn, addr))
            client_thread.start()


def handle_camera(conn, addr):
    global all_streams
    print(f"New connection from {addr}")

    with conn:
        try:
            
            header_id_len = recvall(conn, 4)
            if not header_id_len:
                return
            id_len = struct.unpack(">I", header_id_len)[0]

          
            raw_id = recvall(conn, id_len)
            if not raw_id:
                return
            camera_id = raw_id.decode("utf-8")
            print(f"Camera identified as: {camera_id}")

            while True:
               
                header = recvall(conn, 4)
                if not header:
                    break

                (frame_len,) = struct.unpack(">I", header)

               
                frame_data = recvall(conn, frame_len)
                if not frame_data:
                    break

            
                with streams_lock:
                    all_streams[camera_id] = frame_data

        except Exception as e:
            print(f"Error with {addr}: {e}")
        finally:
            if "camera_id" in locals():
                with streams_lock:
                    all_streams.pop(camera_id, None)
                    print(f"Camera {camera_id} disconnected.")


def generate_stream(camera_id):
    boundary = b"--frame"
    while True:
        frame = all_streams.get(camera_id)
        if frame:
            yield (boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.04)  # ~25 FPS


@app.route("/<camera_id>/stream")
def stream(camera_id):
    if camera_id not in all_streams:
        return "Camera not found", 404
    return Response(
        generate_stream(camera_id), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    
    with streams_lock:
        active = list(all_streams.keys())
    links = "".join([f'<li><a href="/{c}/stream">Camera {c}</a></li>' for c in active])
    return f"<h1>Active Cloud Streams</h1><ul>{links}</ul>"


def recvall(conn, length):
    data = b""
    while len(data) < length:
        chunk = conn.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return data


@app.route("/<camera_id>/snapshot.jpg")
def snapshot(camera_id):
    with streams_lock:
        frame = all_streams.get(camera_id)

    if frame is None:
        abort(404, "Camera not found")

    return send_file(BytesIO(frame), mimetype="image/jpeg", as_attachment=False)


if __name__ == "__main__":
    threading.Thread(target=receiver_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=HTTP_PORT, threaded=True)
