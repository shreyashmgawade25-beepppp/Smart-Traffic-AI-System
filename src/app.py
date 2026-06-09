from flask import Flask, render_template, jsonify
import csv
import os

app = Flask(__name__)

# Absolute CSV path (important)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "results", "traffic_data.csv"))

# -------- LATEST DATA --------
def get_latest_data():
    try:
        if not os.path.exists(CSV_PATH):
            return {"time": "--", "laneA": 0, "laneB": 0, "signal": "--", "countdown": 0}

        with open(CSV_PATH, "r") as file:
            rows = list(csv.reader(file))

            if len(rows) > 1:
                last = rows[-1]
                return {
                    "time": last[0],
                    "laneA": last[1],
                    "laneB": last[2],
                    "signal": last[3],
                    "countdown": last[4]
                }

    except Exception as e:
        print("Error:", e)

    return {"time": "--", "laneA": 0, "laneB": 0, "signal": "--", "countdown": 0}


# -------- GRAPH DATA --------
@app.route("/history")
def history():
    try:
        with open(CSV_PATH, "r") as file:
            rows = list(csv.reader(file))[1:]  # skip header

            rows = rows[-20:]  # last 20 entries

            times = [row[0] for row in rows]
            laneA = [int(row[1]) for row in rows]
            laneB = [int(row[2]) for row in rows]

            return jsonify({
                "times": times,
                "laneA": laneA,
                "laneB": laneB
            })
    except:
        return jsonify({"times": [], "laneA": [], "laneB": []})


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/data")
def data():
    return jsonify(get_latest_data())


if __name__ == "__main__":
    app.run(debug=True)