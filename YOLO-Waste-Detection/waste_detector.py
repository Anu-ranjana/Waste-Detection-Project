"""
Shared YOLOv8 waste-detection helpers used by both the CLI script (detect_camera.py)
and the web app (app.py).
"""

import cv2

CLASS_NAMES = ["Glass", "Metal", "Paper", "Plastic", "Waste"]
BOX_COLOR = (255, 0, 0)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def draw_detections(frame, boxes, classes, confidences) -> None:
    for box, cls, conf in zip(boxes, classes, confidences):
        x1, y1, x2, y2 = map(int, box)
        label = f"{CLASS_NAMES[int(cls)]} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
        (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - text_h - 8), (x1 + text_w + 4, y1), BOX_COLOR, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def detect_frame(model, frame, conf: float):
    """Runs detection on a single BGR frame, draws boxes in place, and returns (frame, detections)."""
    results = model.predict(frame, conf=conf, verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    classes = results[0].boxes.cls.cpu().numpy()
    confidences = results[0].boxes.conf.cpu().numpy()

    draw_detections(frame, boxes, classes, confidences)

    detections = [
        {"class": CLASS_NAMES[int(cls)], "confidence": float(conf_val)}
        for cls, conf_val in zip(classes, confidences)
    ]
    for det in detections:
        print(f"Detected: {det['class']} ({det['confidence']:.2f})")

    return frame, detections
