"""
SMTP email notifications for detection events (image waste/smoking detection
in app.py, and the simulated throwing_waste_detector.py).

Sends an attachment-carrying email per detection. Credentials are read from
environment variables (see .env.example), loaded from a local .env file via
python-dotenv if one is present. Works with Gmail SMTP + an app password, or
any other SMTP server by overriding SMTP_SERVER/SMTP_PORT.
"""

import os
import smtplib
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")


def send_email(subject: str, body: str, attachment_path: str) -> None:
    """Emails `attachment_path` (an image) with the given subject/body.

    Silently skips (with a printed warning) if SMTP credentials aren't
    configured, so detection still works without email set up.
    """
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD or not RECEIVER_EMAIL:
        print("[email] Skipping notification: EMAIL_ADDRESS / EMAIL_APP_PASSWORD / "
              "RECEIVER_EMAIL not set (see .env.example).")
        return

    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(attachment_path, "rb") as f:
        image = MIMEImage(f.read())
        image.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(attachment_path)
        )
        msg.attach(image)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)

    print(f"[email] Sent notification to {RECEIVER_EMAIL}: {subject}")


def send_detection_email(record: dict, snapshot_path: str) -> None:
    """Used by throwing_waste_detector.py: emails a simulated-detection snapshot."""
    subject = f"{record['detection_type']} Detected - {record['video_name']}"
    body = (
        f"Detection type: {record['detection_type']}\n"
        f"Video: {record['video_name']}\n"
        f"Timestamp: {record['timestamp']}\n"
        f"Detected at: {record['detected_at']}\n"
    )
    send_email(subject, body, snapshot_path)


def send_image_detection_email(detection_type: str, detections: list, image_path: str) -> None:
    """Used by app.py's /detect/image route: emails an annotated detection image."""
    label = "Smoking" if detection_type == "smoking" else "Waste"

    counts = {}
    for det in detections:
        counts[det["class"]] = counts.get(det["class"], 0) + 1
    summary = ", ".join(f"{cls} x{count}" for cls, count in counts.items())

    subject = f"{label} Detected"
    body = (
        f"Detection type: {label}\n"
        f"Detected: {summary}\n"
        f"Detected at: {datetime.now().isoformat(timespec='seconds')}\n"
    )
    send_email(subject, body, image_path)
