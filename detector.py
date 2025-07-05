# detector.py

"""Helpers for sending frames to an external AI detection service."""

import os
import requests

import numpy as np
import cv2
try:
    import mss
except ImportError:  # optional when using remote detection
    mss = None

CONFIRMATION_FRAMES = 2
false_count = 0

# Remote AI endpoint (e.g. http://jetson.local:5000/detect)
AI_MODEL_URL = os.getenv("AI_MODEL_URL")

# Define the screen region where the Jetson stream is shown
# You must customize this to your monitor layout
MONITOR_REGION = {
    "top": 100,      # Y position of the top
    "left": 100,     # X position of the left
    "width": 640,    # Width of the stream window
    "height": 480    # Height of the stream window
}

def detect_screenshot():
    global false_count
    if mss is None:
        print("[detector] mss not available for screenshot detection")
        return False

    with mss.mss() as sct:
        frame = np.array(sct.grab(MONITOR_REGION))

    # Convert BGRA to BGR
    frame = frame[:, :, :3]

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([45, 100, 50])
    upper_green = np.array([85, 255, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)
    green_pixels = cv2.countNonZero(mask)

    if green_pixels > 500:
        false_count = 0
        print(f"[detector] ✅ Detected green box (pixels={green_pixels})")
        return True
    else:
        false_count += 1
        if false_count < CONFIRMATION_FRAMES:
            print(f"[detector] 🕓 Holding... ({false_count})")
            return True
        print(f"[detector] ❌ No detection (pixels={green_pixels})")
        return False


def detect_drawing(frame_bytes: bytes | None) -> bool:
    """Send the provided frame to the remote AI model for detection."""
    if frame_bytes is None:
        return False

    if not AI_MODEL_URL:
        # Fallback to screenshot-based detection if no remote URL provided
        return detect_screenshot()

    try:
        resp = requests.post(
            AI_MODEL_URL,
            files={"frame": ("frame.jpg", frame_bytes, "image/jpeg")},
            timeout=2,
        )
        resp.raise_for_status()
        data = resp.json()
        return bool(data.get("drawing"))
    except Exception as e:
        print(f"[detector] Error contacting AI server: {e}")
        return False
