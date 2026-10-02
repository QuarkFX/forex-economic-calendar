import os
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

def read_json_file(filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": f"File {filename} not yet generated. Please wait or run scraper.py."}, 404
    import json
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f), 200

# 1. Forex Factory - This Week
@app.route("/api/forexfactory/thisweek", methods=["GET"])
@app.route("/forexfactory_thisweek.json", methods=["GET"])
def forexfactory_thisweek():
    data, code = read_json_file("forexfactory_thisweek.json")
    return jsonify(data), code

# 2. Forex Factory - 21 Days (3 Weeks)
@app.route("/api/forexfactory/21days", methods=["GET"])
@app.route("/forexfactory_21days.json", methods=["GET"])
def forexfactory_21days():
    data, code = read_json_file("forexfactory_21days.json")
    return jsonify(data), code

# 3. Myfxbook - This Week
@app.route("/api/myfxbook/thisweek", methods=["GET"])
@app.route("/myfxbook_thisweek.json", methods=["GET"])
def myfxbook_thisweek():
    data, code = read_json_file("myfxbook_thisweek.json")
    return jsonify(data), code

# 4. Myfxbook - 21 Days (3 Weeks)
@app.route("/api/myfxbook/21days", methods=["GET"])
@app.route("/myfxbook_21days.json", methods=["GET"])
def myfxbook_21days():
    data, code = read_json_file("myfxbook_21days.json")
    return jsonify(data), code

# Index route listing all 4 endpoints
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "project": "QuarkFX Forex Economic Calendar",
        "description": "Scrapes economic calendar from Forex Factory & Myfxbook every 5 minutes",
        "endpoints": {
            "forexfactory_thisweek": "/api/forexfactory/thisweek",
            "forexfactory_21days": "/api/forexfactory/21days",
            "myfxbook_thisweek": "/api/myfxbook/thisweek",
            "myfxbook_21days": "/api/myfxbook/21days"
        },
        "static_files": {
            "forexfactory_thisweek": "/forexfactory_thisweek.json",
            "forexfactory_21days": "/forexfactory_21days.json",
            "myfxbook_thisweek": "/myfxbook_thisweek.json",
            "myfxbook_21days": "/myfxbook_21days.json"
        }
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
