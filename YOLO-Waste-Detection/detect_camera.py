"""
Waste detection using the trained YOLOv8 model (best_model.pt).

Works with a live webcam, a video file, or a single image.

Usage:
    python detect_camera.py                                  # webcam (index 0)
    python detect_camera.py --source 1                       # webcam index 1
    python detect_camera.py --source path/to/video.mp4        # video file
    python detect_camera.py --source path/to/image.jpg        # image file
    python detect_camera.py --source image.jpg --output out.jpg

Press 'q' to quit a live/video window. Image results close on any key press.
"""

import argparse
import os

import cv2
from ultralytics import YOLO

from waste_detector import IMAGE_EXTENSIONS, detect_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Waste detection from a camera, video, or image.")
    parser.add_argument(
        "--source",
        default="0",
        help="Camera index (e.g. 0, 1), path to a video file, or path to an image file. Default: 0",
    )
    parser.add_argument(
        "--model",
        default="best_model.pt",
        help="Path to the trained YOLO weights. Default: best_model.pt",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for detections. Default: 0.25",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save the annotated result (image or video).",
    )
    return parser.parse_args()


def is_image_source(source: str) -> bool:
    ext = os.path.splitext(source)[1].lower()
    return ext in IMAGE_EXTENSIONS


def open_camera(source: str) -> cv2.VideoCapture:
    # Camera indices are passed as plain digits; anything else is treated as a path/URL.
    cam_source = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(cam_source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")
    return cap


def run_on_image(model: YOLO, source: str, conf: float, output: str) -> None:
    frame = cv2.imread(source)
    if frame is None:
        raise RuntimeError(f"Could not read image: {source}")

    frame, _ = detect_frame(model, frame, conf)

    if output:
        cv2.imwrite(output, frame)
        print(f"Saved result to {output}")

    cv2.imshow("Waste Detection - press any key to close", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def run_on_stream(model: YOLO, source: str, conf: float, output: str) -> None:
    cap = open_camera(source)

    writer = None
    if output:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output, fourcc, fps, (width, height))

    print("Starting detection. Press 'q' to quit.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame, _ = detect_frame(model, frame, conf)

            if writer:
                writer.write(frame)

            cv2.imshow("Waste Detection - press q to quit", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        if writer:
            writer.release()
            print(f"Saved result to {output}")
        cv2.destroyAllWindows()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)

    if is_image_source(args.source):
        run_on_image(model, args.source, args.conf, args.output)
    else:
        run_on_stream(model, args.source, args.conf, args.output)


if __name__ == "__main__":
    main()
