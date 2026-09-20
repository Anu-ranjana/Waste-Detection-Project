"""Detection pipeline shared by the web app.

Wraps the same YOLO + MoveNet + DeepFace logic used in IntegratedArchitecture.py
into a single process_frame() call that a web server can invoke per request,
instead of the original script's dedicated webcam while-loop.
"""
import math
import os
import threading
from datetime import datetime, timedelta

import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
from deepface import DeepFace
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "best.pt")
MOVENET_MODEL_PATH = os.path.join(
    BASE_DIR, "MoveNet", "tflite", "lite-model_movenet_singlepose_lightning_tflite_float16_4.tflite"
)
FACE_DB_PATH = os.path.join(BASE_DIR, "face_database")
FINE_DB_DIR = os.path.join(BASE_DIR, "FineDatabase")
FINE_DB_PATH = os.path.join(FINE_DB_DIR, "fines.xlsx")

CLASS_NAMES = ["bottle", "juice-cup", "nescafe", "plate", "tissue"]
FACE_MODEL_NAME = "Facenet512"
FACE_DISTANCE_METRIC = "euclidean_l2"
LITTERING_THRESHOLD = 100

_yolo_model = YOLO(MODEL_PATH)
_interpreter = tf.lite.Interpreter(model_path=MOVENET_MODEL_PATH)
_interpreter.allocate_tensors()

# YOLO, the tflite interpreter, and DeepFace's Keras models are not safe to call
# from multiple threads at once; Flask's dev server is multi-threaded, so all
# inference is serialized behind this lock.
_inference_lock = threading.Lock()

_fine_lock = threading.Lock()
_last_updated = {}

os.makedirs(FINE_DB_DIR, exist_ok=True)
try:
    _fines_df = pd.read_excel(FINE_DB_PATH)
except FileNotFoundError:
    _fines_df = pd.DataFrame(columns=["Reg_No", "Date", "Fine"])


def _save_fines():
    _fines_df.to_excel(FINE_DB_PATH, index=False)


def _update_fines(name, current_time):
    global _fines_df
    with _fine_lock:
        if name in _fines_df["Reg_No"].values:
            if name not in _last_updated or current_time - _last_updated[name] > timedelta(minutes=2):
                _fines_df.loc[_fines_df["Reg_No"] == name, "Fine"] += 200
                _fines_df.loc[_fines_df["Reg_No"] == name, "Date"] = current_time
                _last_updated[name] = current_time
                _save_fines()
        else:
            new_record = pd.DataFrame([{"Reg_No": name, "Date": current_time, "Fine": 200}])
            _fines_df = pd.concat([_fines_df, new_record], ignore_index=True)
            _last_updated[name] = current_time
            _save_fines()


def _run_pose_inference(image):
    image_width, image_height = image.shape[1], image.shape[0]
    input_size = 192

    input_image = cv2.resize(image, dsize=(input_size, input_size))
    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    input_image = input_image.reshape(-1, input_size, input_size, 3)
    input_image = tf.cast(input_image, dtype=tf.uint8)

    input_details = _interpreter.get_input_details()
    _interpreter.set_tensor(input_details[0]["index"], input_image.numpy())
    _interpreter.invoke()

    output_details = _interpreter.get_output_details()
    keypoints_with_scores = _interpreter.get_tensor(output_details[0]["index"])
    keypoints_with_scores = np.squeeze(keypoints_with_scores)

    keypoints = []
    for index in range(17):
        keypoint_x = int(image_width * keypoints_with_scores[index][1])
        keypoint_y = int(image_height * keypoints_with_scores[index][0])
        keypoints.append([keypoint_x, keypoint_y])
    return keypoints


def _calculate_lengths(p1, p2, x1, y1):
    len_left = math.hypot(p1[0] - x1, p1[1] - y1)
    len_right = math.hypot(p2[0] - x1, p2[1] - y1)
    return len_left, len_right


def process_frame(frame, enable_face_recognition=True):
    """Run object detection, pose estimation and (optionally) face recognition
    on a single BGR frame, drawing overlays in place.

    Returns (annotated_frame, events) where events is a JSON-serializable list
    describing any littering incidents found in this frame.
    """
    events = []

    with _inference_lock:
        people = []
        if enable_face_recognition:
            try:
                people = DeepFace.find(
                    img_path=frame,
                    db_path=FACE_DB_PATH,
                    model_name=FACE_MODEL_NAME,
                    distance_metric=FACE_DISTANCE_METRIC,
                    enforce_detection=False,
                    silent=True,
                )
            except Exception:
                people = []

        predictions = _yolo_model(frame, stream=True, verbose=False)

        keypoints = None
        for r in predictions:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 2)
                conf = math.ceil((box.conf[0] * 100)) / 100
                cls = int(box.cls[0])
                class_name = CLASS_NAMES[cls] if cls < len(CLASS_NAMES) else str(cls)
                cv2.putText(
                    frame, f"{class_name}: {conf}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2,
                )

                if keypoints is None:
                    keypoints = _run_pose_inference(frame)
                p1, p2 = tuple(keypoints[9]), tuple(keypoints[10])
                cv2.circle(frame, p1, 6, (255, 255, 255), -1)
                cv2.circle(frame, p2, 6, (255, 255, 255), -1)

                len_left, len_right = _calculate_lengths(p1, p2, x1, y1)
                if len_right > len_left:
                    cv2.line(frame, p1, (x1, y1), (0, 0, 0), 1)
                    length = len_left
                else:
                    cv2.line(frame, p2, (x1, y1), (0, 0, 0), 1)
                    length = len_right

                if length > LITTERING_THRESHOLD:
                    for person_df in people:
                        if person_df.empty:
                            continue
                        person = person_df.iloc[0]
                        px, py, pw, ph = (
                            int(person["source_x"]), int(person["source_y"]),
                            int(person["source_w"]), int(person["source_h"]),
                        )
                        name = os.path.basename(os.path.dirname(person["identity"]))

                        cv2.rectangle(frame, (px, py), (px + pw, py + ph), (0, 255, 0), 2)
                        cv2.putText(
                            frame, "Potential Litterer Detected",
                            (int(px - pw / 2), int(py - ph / 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2,
                        )

                        if name != "Unknown":
                            _update_fines(name, datetime.now())

                        events.append({
                            "object": class_name,
                            "confidence": conf,
                            "person": name,
                        })

    return frame, events
