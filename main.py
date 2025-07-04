import os
import cv2
import numpy as np
import jetson.inference
import jetson.utils
import onnxruntime as ort
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# === Config ===
LABELS = ["cat", "dog", "tree", "car", "house"]  # Update to your class list
ONNX_PATH = "models/quickdraw.onnx"
SAVE_DIR = "static/snapshots"
CONFIDENCE_THRESHOLD = 0.6

# === Initialize ===
os.makedirs(SAVE_DIR, exist_ok=True)

# Load ONNX classifier
session = ort.InferenceSession(ONNX_PATH)
input_name = session.get_inputs()[0].name
input_shape = session.get_inputs()[0].shape  # [1, 3, 224, 224]

# Load custom-trained pen/hand detection model
detector = jetson.inference.detectNet("custom", threshold=0.5)

# Flask app setup
app = Flask(__name__)
latest = {"label": "", "confidence": 0.0, "path": ""}

# === Utils ===
def preprocess(img):
    img = cv2.resize(img, (input_shape[2], input_shape[3]))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    return img

def classify(img_bgr):
    input_tensor = preprocess(img_bgr)
    outputs = session.run(None, {input_name: input_tensor})
    probs = outputs[0][0]
    idx = int(np.argmax(probs))
    return LABELS[idx], float(probs[idx])

def save_snapshot(img, label):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{timestamp}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(filepath, img)
    return filename

# === Web Routes ===
@app.route("/")
def index():
    return render_template("index.html", pred=latest)

@app.route("/correct", methods=["POST"])
def correct():
    data = request.json
    new_label = data["label"]
    old_name = latest["path"].split("/")[-1]
    old_path = os.path.join(SAVE_DIR, old_name)
    if os.path.exists(old_path):
        new_name = old_name.replace("uncertain", new_label)
        new_path = os.path.join(SAVE_DIR, new_name)
        os.rename(old_path, new_path)
        latest["path"] = f"/static/snapshots/{new_name}"
    return jsonify(success=True, new_label=new_label)

# === AI Thread ===
def ai_loop():
    global latest
    cam = jetson.utils.gstCamera(640, 480, "/dev/video0")
    drawing = False

    while True:
        img, w, h = cam.CaptureRGBA(zeroCopy=1)
        detections = detector.Detect(img, w, h)
        np_img = jetson.utils.cudaToNumpy(img, w, h).astype(np.uint8)
        frame = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)

        pen_detected = any(d.ClassID == detector.GetClassID("pen") or d.ClassID == detector.GetClassID("hand") for d in detections)

        if pen_detected and not drawing:
            print("[INFO] Drawing started.")
            drawing = True

        elif not pen_detected and drawing:
            print("[INFO] Drawing ended. Classifying...")
            drawing = False
            label, conf = classify(frame)
            latest["label"] = label
            latest["confidence"] = conf

            if conf < CONFIDENCE_THRESHOLD:
                file = save_snapshot(frame, "uncertain")
                latest["path"] = f"/static/snapshots/{file}"
            else:
                latest["path"] = ""
                print(f"[OK] Predicted: {label} ({conf:.2f})")

# === Launch ===
if __name__ == "__main__":
    import threading
    print("[BOOT] Starting LiveArt AI and web server.")
    thread = threading.Thread(target=ai_loop, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000)
