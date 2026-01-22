from flask import Flask, request, send_from_directory, jsonify, make_response
import os
from pathlib import Path
import yt_dlp
from threading import Thread
import time

app = Flask(__name__)
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# ----------------------------
# Cleanup old files
# ----------------------------
def cleanup_task():
    while True:
        now = time.time()
        for f in AUDIO_DIR.iterdir():
            if f.is_file() and now - f.stat().st_mtime > 3600:  # 1 hour
                f.unlink()
        time.sleep(600)  # every 10 min

Thread(target=cleanup_task, daemon=True).start()

# ----------------------------
# Download song from YouTube
# ----------------------------
def download_song(song_name):
    safe_name = song_name.replace(" ", "_")
    file_path = AUDIO_DIR / f"{safe_name}.mp3"
    if file_path.exists():
        return file_path.name

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(AUDIO_DIR / f"{safe_name}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
    }

    # Search YouTube
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            return f"{safe_name}.mp3"
        except Exception as e:
            print(f"Download error: {e}")
            return None

# ----------------------------
# API to fetch song
# ----------------------------
@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    filename = download_song(query)
    if not filename:
        return jsonify({"error": "Failed to fetch"}), 500

    return jsonify({"url": f"/audio/{filename}"})

# ----------------------------
# Serve audio files
# ----------------------------
@app.route("/audio/<path:filename>")
def serve_audio(filename):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        return "File not found", 404

    resp = make_response(send_from_directory(AUDIO_DIR, filename))
    resp.headers["Content-Type"] = "audio/mpeg"
    resp.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp

# ----------------------------
# Run server
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
