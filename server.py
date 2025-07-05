from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import jetson.inference
import jetson.utils

app = Flask(__name__)

# Load your detection model once
net = jetson.inference.detectNet(
    model="models/ssd-mobilenet.onnx",
    labels="models/labels.txt",
    input_blob="input_0",
    output_cvg="scores",
    output_bbox="boxes",
    threshold=0.5  # optional: adjust detection confidence threshold
)

@app.route('/detect', methods=['POST'])
def detect():
    if 'frame' not in request.files:
        return jsonify({'error': 'No frame provided'}), 400

    file = request.files['frame']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # Convert to RGBA and CUDA memory for Jetson
    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    img_cuda = jetson.utils.cudaFromNumpy(img_rgba)

    # Run detection
    detections = net.Detect(img_cuda)

    # Check for specific class (e.g. "drawing")
    found = any(det.ClassID == net.GetClassID("drawing") for det in detections)

    return jsonify({"drawing": found})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
