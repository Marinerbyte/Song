from flask import Flask, request, jsonify
import os
import requests
import threading
import time
from pathlib import Path

app = Flask(__name__)
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# --------------------------
# Background cleanup
# --------------------------
def cleanup_loop():
    while True:
        now = time.time()
        for f in AUDIO_DIR.glob("*.mp3"):
            if now - f.stat().st_mtime > 3600:  # 1 hour purani files delete
                f.unlink()
        time.sleep(600)  # 10 min interval

threading.Thread(target=cleanup_loop, daemon=True).start()

# --------------------------
# Simulated Song Search
# --------------------------
def download_song(song_name):
    """
    Placeholder function
    Real version me external lightweight source ya archive/telegram API se download
    """
    filename = AUDIO_DIR / f"{song_name.replace(' ','_')}.mp3"
    
    if not filename.exists():
        # Simulate small mp3 file (for testing)
        with open(filename, "wb") as f:
            f.write(b"\x00" * 1024)  # 1KB dummy file
    
    return filename.name

# --------------------------
# API: Search + Fetch
# --------------------------
@app.route("/api/search", methods=["POST"])
def search_song():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing query"}), 400
    
    song_name = data["query"]
    file_name = download_song(song_name)
    return jsonify({"url": f"/audio/{file_name}"})

@app.route("/api/fetch", methods=["POST"])
def fetch_song():
    data = request.get_json()
    if not data or "file_id" not in data:
        return jsonify({"error": "Missing file_id"}), 400
    
    file_id = data["file_id"]
    # In this simple version, file_id = song name
    file_name = download_song(file_id)
    return jsonify({"url": f"/audio/{file_name}"})

# --------------------------
# Serve audio files
# --------------------------
from flask import send_from_directory

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

# --------------------------
# Run app
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
