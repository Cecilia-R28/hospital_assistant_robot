from flask import Flask, jsonify, render_template, request

from catalog import CATALOG, INFO_DISCLAIMER
from requests_model import build_request

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", catalog=CATALOG)


@app.route("/api/request", methods=["POST"])
def api_request():
    data = request.get_json(silent=True) or {}
    try:
        structured = build_request(data.get("category"), data.get("item"))
    except ValueError as err:
        return jsonify({"ok": False, "error": str(err)}), 400
    entry = CATALOG[data["category"]]
    item = entry["items"][data["item"]]
    if "info" in item:
        title = item["label"]
        message = item["info"] + "\n\n" + INFO_DISCLAIMER
    else:
        title = "Votre choix"
        message = entry["confirm"].format(label=item["label"])
    return jsonify({"ok": True, "request": structured, "title": title, "message": message})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
