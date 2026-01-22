import os
import time
import threading
import requests
from flask import Flask, jsonify, send_from_directory, request

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
AUDIO_DIR = "audio"
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
AUTO_DELETE_AFTER = 30 * 60       # 30 minutes

os.makedirs(AUDIO_DIR, exist_ok=True)
app = Flask(__name__)

def auto_delete(filepath):
    time.sleep(AUTO_DELETE_AFTER)
    if os.path.exists(filepath):
        os.remove(filepath)

@app.route("/api/fetch", methods=["POST"])
def fetch_from_telegram():
    data = request.get_json() or {}
    file_id = data.get("file_id")
    if not file_id:
        return jsonify({"error": "file_id missing"}), 400

    r = requests.get(f"{BASE_URL}/getFile", params={"file_id": file_id}).json()
    if not r.get("ok"):
        return jsonify({"error": "telegram getFile failed"}), 500

    file_path = r["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

    resp = requests.get(file_url, stream=True)
    size = int(resp.headers.get("Content-Length", 0))
    if size > MAX_FILE_SIZE:
        return jsonify({"error": "file too large"}), 413

    filename = f"{int(time.time())}.mp3"
    save_path = os.path.join(AUDIO_DIR, filename)
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(1024):
            f.write(chunk)

    threading.Thread(target=auto_delete, args=(save_path,), daemon=True).start()

    return jsonify({
        "url": f"/audio/{filename}"
    })

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename, mimetype="audio/mpeg", as_attachment=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
