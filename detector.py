# detector.py

import numpy as np
import cv2
import mss

CONFIRMATION_FRAMES = 2
false_count = 0

# Define the screen region where the Jetson stream is shown
# You must customize this to your monitor layout
MONITOR_REGION = {
    "top": 100,      # Y position of the top
    "left": 100,     # X position of the left
    "width": 640,    # Width of the stream window
    "height": 480    # Height of the stream window
}

def detect_drawing():
    global false_count
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
