"""
Shared YOLOv5 smoking/cigarette-detection helpers used by app.py.

The model (smoking_model.pt) is a legacy YOLOv5 checkpoint from
https://github.com/AarnoStormborn/Smoking-Detection, trained on a single
"cigarette" class. ultralytics.YOLO() can't load YOLOv5 checkpoints directly,
so it's loaded via torch.hub in app.py instead; this module just mirrors the
detect_frame(model, frame, conf) -> (frame, detections) interface used by
waste_detector.py so both models are interchangeable.
"""

import cv2

CLASS_NAMES = ["Cigarette"]
BOX_COLOR = (0, 140, 255)


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
    model.conf = conf
    results = model(frame)
    preds = results.xyxy[0].cpu().numpy()  # columns: x1, y1, x2, y2, confidence, class

    boxes = preds[:, :4]
    confidences = preds[:, 4]
    classes = preds[:, 5]

    draw_detections(frame, boxes, classes, confidences)

    detections = [
        {"class": CLASS_NAMES[int(cls)], "confidence": float(conf_val)}
        for cls, conf_val in zip(classes, confidences)
    ]
    for det in detections:
        print(f"Detected: {det['class']} ({det['confidence']:.2f})")

    return frame, detections
