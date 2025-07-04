# app.py

from flask import Flask, render_template, request, jsonify
import threading
import time
import detector
import spotify
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# === App State ===
drawing_active = False
last_trigger_time = 0
TRIGGER_COOLDOWN = 10  # seconds

# === Detection Thread ===
def monitor_drawing():
    global drawing_active, last_trigger_time

    LEINENCY_SECONDS = 8
    last_seen_drawing = 0
    music_playing = False

    while True:
        detected = detector.detect_drawing()
        now = time.time()

        if detected:
            last_seen_drawing = now
            if not music_playing:
                print("[LiveArt] Drawing detected — starting music.")
                spotify.start_music()
                music_playing = True
            drawing_active = True
        else:
            time_since_last = now - last_seen_drawing
            if time_since_last > LEINENCY_SECONDS and music_playing:
                print("[LiveArt] No drawing detected — pausing music.")
                spotify.pause()
                music_playing = False
                drawing_active = False

        time.sleep(0.5)  # Adjust for sensitivity

# === Routes ===
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/spotify", methods=["POST"])
def control_spotify():
    data = request.json
    action = data.get("action")
    uri = data.get("uri")

    match action:
        case "play":
            spotify.play()
        case "pause":
            spotify.pause()
        case "next":
            spotify.next_track()
        case "previous":
            spotify.previous_track()
        case "toggle_shuffle":
            spotify.toggle_shuffle()
        case "toggle_repeat":
            spotify.toggle_repeat()
        case "play_playlist":
            spotify.play_playlist(uri)
        case _:
            return jsonify({"error": "Unknown action"}), 400

    return jsonify({"status": "ok"})

@app.route("/status")
def status():
    return jsonify({
        "drawing": drawing_active,
        "last_trigger": last_trigger_time
    })

@app.route("/spotify/status")
def now_playing():
    return jsonify(spotify.get_now_playing())


# === Main ===
if __name__ == "__main__":
    threading.Thread(target=monitor_drawing, daemon=True).start()
    app.run(debug=True)
