import os
from flask import Flask, jsonify, Response

app = Flask(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Cache-Control"] = "public, max-age=60, s-maxage=60, stale-while-revalidate=30"
    return response

def serve_json(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": f"{filename} not found. Run scripts/scraper.py first."}), 404
    with open(filepath, "r", encoding="utf-8") as f:
        return Response(f.read(), mimetype="application/json")

@app.route("/api/forexfactory/21days")
@app.route("/forexfactory_21days.json")
def ff_21days():
    return serve_json("forexfactory_21days.json")

@app.route("/api/myfxbook/21days")
@app.route("/myfxbook_21days.json")
def mfb_21days():
    return serve_json("myfxbook_21days.json")

@app.route("/api/forexfactory/thisweek")
@app.route("/forexfactory_thisweek.json")
def ff_thisweek():
    return serve_json("forexfactory_thisweek.json")

@app.route("/api/myfxbook/thisweek")
@app.route("/myfxbook_thisweek.json")
def mfb_thisweek():
    return serve_json("myfxbook_thisweek.json")

@app.route("/")
def index():
    return jsonify({
        "project": "QuarkFX Forex Economic Calendar",
        "status": "online",
        "endpoints": {
            "forexfactory_21days": "/api/forexfactory/21days",
            "myfxbook_21days": "/api/myfxbook/21days",
            "forexfactory_thisweek": "/api/forexfactory/thisweek",
            "myfxbook_thisweek": "/api/myfxbook/thisweek"
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
