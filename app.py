"""
AI锁屏图片生成器 - Flask Backend
荣耀魔法画报 · 智能内容生产平台

部署到 Render / Heroku 等 PaaS 平台。
"""

import json
import os
import time
import urllib.request
import urllib.error

from flask import Flask, request, jsonify, send_from_directory

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("MULEROUTER_API_KEY", "")
BASE_URL = os.environ.get("MULEROUTER_BASE_URL", "")
SITE = os.environ.get("MULEROUTER_SITE", "")

if not BASE_URL:
    if SITE.lower() == "mulerouter":
        BASE_URL = "https://api.mulerouter.ai"
    elif SITE.lower() == "mulerun":
        BASE_URL = "https://api.mulerun.com"
    else:
        BASE_URL = "https://api.mulerun.com"  # default

MODEL_PATH = "vendors/google/v1/nano-banana-pro/generation"
FALLBACK_MODEL_PATH = "vendors/google/v1/nano-banana/generation"

MAX_WAIT = 300

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "MuleRouter-AgentSkill/1.0.0",
    "X-Agent-Skills": "mulerouter",
}

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def api_request(method, url, data=None, timeout=120):
    """Make an authenticated API request."""
    headers = {**HEADERS, "Authorization": f"Bearer {API_KEY}"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def create_task(prompt, aspect_ratio="9:16", model_path=MODEL_PATH):
    """Create an image generation task."""
    url = f"{BASE_URL}/{model_path}"
    payload = {"prompt": prompt, "aspect_ratio": aspect_ratio}
    if "nano-banana-pro" in model_path:
        payload["resolution"] = "2K"
    resp = api_request("POST", url, payload)
    task_id = resp.get("task_info", {}).get("id")
    if not task_id:
        raise RuntimeError(f"No task_id: {json.dumps(resp)[:200]}")
    return task_id, model_path


def poll_task(task_id, model_path):
    """Poll until task completes. Uses aggressive early polling then backs off."""
    url = f"{BASE_URL}/{model_path}/{task_id}"
    start = time.time()
    attempt = 0
    while True:
        if time.time() - start > MAX_WAIT:
            raise TimeoutError("Timed out")
        resp = api_request("GET", url)
        status = resp.get("task_info", {}).get("status", "").lower()
        if status in ("completed", "succeeded"):
            images = resp.get("images") or resp.get("results") or []
            if images:
                return images
            raise RuntimeError("No images returned")
        if status == "failed":
            err = resp.get("task_info", {}).get("error", {})
            raise RuntimeError(err.get("detail") or err.get("title") or str(err))
        # Aggressive early polling: 2s for first 5 attempts, then 5s
        attempt += 1
        wait = 2 if attempt <= 5 else 5
        time.sleep(wait)


def generate_image(prompt, aspect_ratio="9:16"):
    """Full flow: create → poll → return URL."""
    try:
        task_id, mp = create_task(prompt, aspect_ratio, MODEL_PATH)
    except Exception:
        task_id, mp = create_task(prompt, aspect_ratio, FALLBACK_MODEL_PATH)
    images = poll_task(task_id, mp)
    return {"success": True, "image_url": images[0], "task_id": task_id}


# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    try:
        body = request.get_json(force=True)
        prompt = body.get("prompt", "")
        aspect_ratio = body.get("aspect_ratio", "9:16")
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400
        result = generate_image(prompt, aspect_ratio)
        return jsonify(result)
    except TimeoutError:
        return jsonify({"success": False, "error": "图片生成超时，请重试"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
