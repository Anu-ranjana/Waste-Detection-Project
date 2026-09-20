"""
Flask web app for waste and smoking detection: upload an image, upload a video,
or use a live camera feed. Uses the trained YOLOv8 waste model (best_model.pt)
and YOLOv5 smoking model (smoking_model.pt), via the shared helpers in
waste_detector.py and smoking_detector.py.

Usage:
    python app.py
    (then open http://127.0.0.1:5000 in a browser)
"""

import os
import uuid

import cv2
import imageio.v2 as imageio
import numpy as np
import torch
from flask import Flask, Response, jsonify, render_template, request
from ultralytics import YOLO
from werkzeug.utils import secure_filename

from email_notifier import send_image_detection_email
from smoking_detector import detect_frame as detect_frame_smoking
from throwing_waste_detector import VIDEOS_DIR as THROWING_WASTE_VIDEOS_DIR
from throwing_waste_detector import load_log as load_throwing_waste_log
from throwing_waste_detector import process_events as run_throwing_waste_detector
from throwing_waste_detector import reset_log as reset_throwing_waste_log
from waste_detector import detect_frame as detect_frame_waste

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_model.pt")
SMOKING_MODEL_PATH = os.path.join(BASE_DIR, "smoking_model.pt")
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "outputs")
CONF_THRESHOLD = 0.25
SMOKING_CONF_THRESHOLD = 0.25

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
model = YOLO(MODEL_PATH)

# smoking_model.pt is a legacy YOLOv5 checkpoint, which ultralytics.YOLO() can't
# load directly, so it's loaded via torch.hub's YOLOv5 loader instead. The first
# run needs internet access to fetch/cache the YOLOv5 hub code; later runs use
# the local torch.hub cache.
smoking_model = torch.hub.load(
    "ultralytics/yolov5", "custom", path=SMOKING_MODEL_PATH, trust_repo=True
)

# Registry mapping a detection "type" to its (model, detect_fn, conf_threshold).
# Both detect_fn implementations share the detect_frame(model, frame, conf) ->
# (frame, detections) signature, so routes below can stay type-agnostic.
DETECTORS = {
    "waste": (model, detect_frame_waste, CONF_THRESHOLD),
    "smoking": (smoking_model, detect_frame_smoking, SMOKING_CONF_THRESHOLD),
}


def get_detector(detection_type):
    return DETECTORS.get(detection_type, DETECTORS["waste"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/detect/image", methods=["POST"])
def detect_image():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    detection_type = request.form.get("type", "waste")
    det_model, detect_fn, conf = get_detector(detection_type)

    data = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Could not decode image"}), 400

    frame, detections = detect_fn(det_model, frame, conf)

    filename = f"{uuid.uuid4().hex}.jpg"
    out_path = os.path.join(OUTPUT_DIR, filename)
    cv2.imwrite(out_path, frame)

    if detections:
        try:
            send_image_detection_email(detection_type, detections, out_path)
        except Exception as exc:
            print(f"[email-error] failed to send image detection notification: {exc}")

    return jsonify({
        "result_url": f"/static/outputs/{filename}",
        "detections": detections,
    })


@app.route("/detect/video", methods=["POST"])
def detect_video():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    det_model, detect_fn, conf = get_detector(request.form.get("type", "waste"))

    upload_id = uuid.uuid4().hex
    in_path = os.path.join(OUTPUT_DIR, f"{upload_id}_in.mp4")
    out_filename = f"{upload_id}_out.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_filename)
    file.save(in_path)

    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        os.remove(in_path)
        return jsonify({"error": "Could not read video"}), 400

    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    # H.264 + yuv420p + faststart so the result plays inline in browsers
    # (OpenCV's own VideoWriter codecs, e.g. mp4v, aren't browser-playable).
    writer = imageio.get_writer(
        out_path,
        fps=fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        output_params=["-movflags", "+faststart"],
    )

    class_counts = {}
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame, detections = detect_fn(det_model, frame, conf)
            for det in detections:
                class_counts[det["class"]] = class_counts.get(det["class"], 0) + 1
            writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        cap.release()
        writer.close()
        os.remove(in_path)

    return jsonify({
        "result_url": f"/static/outputs/{out_filename}",
        "summary": class_counts,
    })


def gen_camera_frames(camera_index: int, det_model, detect_fn, conf: float):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame, _ = detect_fn(det_model, frame, conf)

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )
    finally:
        cap.release()


@app.route("/video_feed")
def video_feed():
    camera_index = request.args.get("camera", default=0, type=int)
    det_model, detect_fn, conf = get_detector(request.args.get("type", "waste"))
    return Response(
        gen_camera_frames(camera_index, det_model, detect_fn, conf),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/throwing-waste/videos")
def throwing_waste_videos():
    names = sorted(
        f for f in os.listdir(THROWING_WASTE_VIDEOS_DIR)
        if os.path.isfile(os.path.join(THROWING_WASTE_VIDEOS_DIR, f)) and not f.startswith(".")
    )
    return jsonify(names)


THROWING_WASTE_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@app.route("/throwing-waste/upload", methods=["POST"])
def throwing_waste_upload():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    if os.path.splitext(filename)[1].lower() not in THROWING_WASTE_VIDEO_EXTENSIONS:
        return jsonify({"error": "Unsupported file type. Upload a video file (.mp4, .avi, .mov, .mkv, .webm)."}), 400

    file.save(os.path.join(THROWING_WASTE_VIDEOS_DIR, filename))
    return jsonify({"video_name": filename})


@app.route("/throwing-waste/detections")
def throwing_waste_detections():
    records = load_throwing_waste_log()
    records.sort(key=lambda r: r["detected_at"], reverse=True)
    return jsonify(records)


@app.route("/throwing-waste/run", methods=["POST"])
def throwing_waste_run():
    try:
        created = run_throwing_waste_detector()
    except FileNotFoundError:
        return jsonify({"error": "Events file not found: data/throwing_waste_events.json"}), 400
    return jsonify({"created": len(created)})


@app.route("/throwing-waste/reset", methods=["POST"])
def throwing_waste_reset():
    cleared = reset_throwing_waste_log()
    return jsonify({"cleared": cleared})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
