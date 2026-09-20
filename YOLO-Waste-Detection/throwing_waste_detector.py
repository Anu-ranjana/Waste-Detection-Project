"""
Simulated ("fake") throwing-waste detector.

There is no real model behind this yet. Instead of running inference, it
reads a JSON file (data/throwing_waste_events.json) that says which uploaded
video "detected" a throwing-waste event and at what timestamp, then:

  1. Locates the matching video in uploads/videos/.
  2. Extracts a snapshot frame at that timestamp with ffmpeg.
  3. Saves the snapshot under static/outputs/throwing_waste_snapshots/.
  4. Appends the detection event to data/throwing_waste_log.json, the
     persistent store the dashboard (see app.py's /throwing-waste routes)
     reads from.
  5. Emails the snapshot via email_notifier.send_detection_email.

This mirrors the shared detect_frame(model, frame, conf) module pattern used
by waste_detector.py / smoking_detector.py, just swapping "run a model on a
frame" for "read a scripted event and manufacture the same kind of result".

Usage:
    python throwing_waste_detector.py
    python throwing_waste_detector.py --events path/to/events.json
"""

import argparse
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime

import imageio_ffmpeg

from email_notifier import send_detection_email

# app.py already depends on imageio (for browser-playable video output), which
# pulls in imageio-ffmpeg and its bundled ffmpeg binary. Prefer a "ffmpeg" on
# PATH if present, otherwise fall back to that bundled binary so this works
# without a separate system-wide ffmpeg install.
FFMPEG_EXE = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "uploads", "videos")
EVENTS_FILE = os.path.join(BASE_DIR, "data", "throwing_waste_events.json")
LOG_FILE = os.path.join(BASE_DIR, "data", "throwing_waste_log.json")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "static", "outputs", "throwing_waste_snapshots")
DETECTION_TYPE = "Throwing Waste"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def load_events(events_path: str) -> list:
    with open(events_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_log() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_log(records: list) -> None:
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def reset_log() -> int:
    """Clears the detection log and deletes the snapshots it referenced. Returns the number of records cleared."""
    records = load_log()
    for record in records:
        rel_path = record["snapshot_url"].lstrip("/")
        snapshot_path = os.path.join(BASE_DIR, *rel_path.split("/"))
        if os.path.exists(snapshot_path):
            os.remove(snapshot_path)
    save_log([])
    return len(records)


def extract_snapshot(video_path: str, timestamp: str, out_path: str) -> None:
    """Extracts a single frame at `timestamp` (HH:MM:SS) from `video_path` via ffmpeg."""
    cmd = [
        FFMPEG_EXE, "-y",
        "-ss", timestamp,
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        out_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg executable not found. Install ffmpeg and ensure it's on PATH."
        ) from exc

    if result.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError(
            f"ffmpeg failed to extract frame at {timestamp} from {video_path}: "
            f"{result.stderr.strip()}"
        )


def process_events(events_path: str = EVENTS_FILE) -> list:
    """Runs the simulated detector over `events_path` and returns the newly created records."""
    events = load_events(events_path)
    log = load_log()
    new_records = []

    for video_entry in events:
        video_name = video_entry["video_name"]
        video_path = os.path.join(VIDEOS_DIR, video_name)
        if not os.path.exists(video_path):
            print(f"[skip] video not found in uploads/videos/: {video_name}")
            continue

        for detection in video_entry.get("detections", []):
            timestamp = detection["timestamp"]
            safe_ts = timestamp.replace(":", "-")
            snapshot_name = (
                f"{os.path.splitext(video_name)[0]}_{safe_ts}_{uuid.uuid4().hex[:8]}.jpg"
            )
            snapshot_path = os.path.join(SNAPSHOT_DIR, snapshot_name)

            try:
                extract_snapshot(video_path, timestamp, snapshot_path)
            except RuntimeError as exc:
                print(f"[error] {exc}")
                continue

            record = {
                "video_name": video_name,
                "timestamp": timestamp,
                "detection_type": DETECTION_TYPE,
                "snapshot_url": f"/static/outputs/throwing_waste_snapshots/{snapshot_name}",
                "detected_at": datetime.now().isoformat(timespec="seconds"),
            }
            log.append(record)
            new_records.append(record)
            print(f"[detected] {video_name} @ {timestamp} -> {snapshot_name}")

            try:
                send_detection_email(record, snapshot_path)
            except Exception as exc:
                print(f"[email-error] {video_name} @ {timestamp}: {exc}")

    save_log(log)
    return new_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the simulated throwing-waste detector over a JSON events file."
    )
    parser.add_argument(
        "--events",
        default=EVENTS_FILE,
        help="Path to the events JSON file. Default: data/throwing_waste_events.json",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the detection log and its snapshots instead of running the detector.",
    )
    args = parser.parse_args()

    if args.reset:
        cleared = reset_log()
        print(f"Done. {cleared} record(s) cleared.")
    else:
        created = process_events(args.events)
        print(f"Done. {len(created)} new detection(s) logged.")
