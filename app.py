from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading
import time

app = Flask(__name__)

# Folder jahan songs save honge
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# ------------------------
# Cleanup Thread (Old Files)
# ------------------------
def cleanup_old_files(interval=3600):
    while True:
        now = time.time()
        for f in os.listdir(AUDIO_DIR):
            path = os.path.join(AUDIO_DIR, f)
            if os.path.isfile(path):
                if now - os.path.getmtime(path) > interval:  # 1 hour
                    try:
                        os.remove(path)
                        print(f"[Cleanup] Deleted {f}")
                    except:
                        pass
        time.sleep(interval // 2)  # Half interval sleep

threading.Thread(target=cleanup_old_files, daemon=True).start()

# ------------------------
# Routes
# ------------------------
@app.route("/api/search", methods=["POST"])
def search_song():
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query"}), 400

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{AUDIO_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch1:{query}", download=True)
            info = result['entries'][0]
            filename = ydl.prepare_filename(info)
            mp3_file = os.path.splitext(filename)[0] + ".mp3"

        file_id = uuid.uuid4().hex
        return jsonify({
            "url": f"/audio/{os.path.basename(mp3_file)}",
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=False)
    return "File not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
