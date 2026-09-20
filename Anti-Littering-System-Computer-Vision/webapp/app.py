import base64
import os
import threading
import uuid

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template, request

from pipeline import process_frame

app = Flask(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_video_jobs = {}
_jobs_lock = threading.Lock()


def _decode_upload(file_storage):
    data = np.frombuffer(file_storage.read(), np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _encode_jpeg_b64(frame):
    ok, buf = cv2.imencode(".jpg", frame)
    if not ok:
        return None
    return base64.b64encode(buf).decode("utf-8")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process-image", methods=["POST"])
def api_process_image():
    file = request.files.get("image")
    if file is None:
        return jsonify({"error": "No image uploaded"}), 400

    frame = _decode_upload(file)
    if frame is None:
        return jsonify({"error": "Could not decode image"}), 400

    annotated, events = process_frame(frame)
    encoded = _encode_jpeg_b64(annotated)
    if encoded is None:
        return jsonify({"error": "Could not encode result"}), 500

    return jsonify({"image": encoded, "events": events})


@app.route("/api/process-frame", methods=["POST"])
def api_process_frame():
    """Used by the browser camera view: one JPEG data-URL frame in, one annotated frame out."""
    payload = request.get_json(silent=True) or {}
    data_url = payload.get("image", "")
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]

    try:
        raw = base64.b64decode(data_url)
    except Exception:
        return jsonify({"error": "Invalid image data"}), 400

    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Could not decode frame"}), 400

    annotated, events = process_frame(frame)
    encoded = _encode_jpeg_b64(annotated)
    if encoded is None:
        return jsonify({"error": "Could not encode result"}), 500

    return jsonify({"image": encoded, "events": events})


@app.route("/api/upload-video", methods=["POST"])
def api_upload_video():
    file = request.files.get("video")
    if file is None:
        return jsonify({"error": "No video uploaded"}), 400

    token = uuid.uuid4().hex
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        ext = ".mp4"
    path = os.path.join(UPLOAD_DIR, f"{token}{ext}")
    file.save(path)

    with _jobs_lock:
        _video_jobs[token] = path

    return jsonify({"token": token})


def _gen_video_stream(path):
    cap = cv2.VideoCapture(path)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            annotated, _ = process_frame(frame)
            ok, buf = cv2.imencode(".jpg", annotated)
            if not ok:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
            )
    finally:
        cap.release()
        try:
            os.remove(path)
        except OSError:
            pass


@app.route("/api/video-stream/<token>")
def api_video_stream(token):
    with _jobs_lock:
        path = _video_jobs.pop(token, None)

    if path is None or not os.path.exists(path):
        return "Not found", 404

    return Response(_gen_video_stream(path), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
