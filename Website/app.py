from datetime import datetime
import sqlite3
from statistics import mean

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)
DB_PATH = "smart_crop.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moisture REAL NOT NULL,
            temperature REAL,
            humidity REAL,
            captured_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS crop_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            planting_date TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def analog_to_percent(raw_value):
    # 4095 -> 0% (dry), 0 -> 100% (wet) for common capacitive sensor mapping.
    raw = max(0.0, min(float(raw_value), 4095.0))
    return round((4095.0 - raw) / 4095.0 * 100.0, 2)


def get_planting_date(conn):
    row = conn.execute("SELECT planting_date FROM crop_config WHERE id = 1").fetchone()
    if row:
        return datetime.strptime(row["planting_date"], "%Y-%m-%d").date()
    return None


def predict_lifecycle(days_since_planting, avg_moisture):
    # Stage progression with simple moisture stress correction.
    stress_days = 0
    if avg_moisture < 30:
        stress_days = 10
    elif avg_moisture < 45:
        stress_days = 5

    effective_days = max(0, days_since_planting - stress_days)

    if effective_days <= 14:
        stage = "Germination"
        next_stage = "Vegetative"
        days_to_next = 15 - effective_days
    elif effective_days <= 45:
        stage = "Vegetative"
        next_stage = "Flowering"
        days_to_next = 46 - effective_days
    elif effective_days <= 75:
        stage = "Flowering"
        next_stage = "Fruiting"
        days_to_next = 76 - effective_days
    elif effective_days <= 110:
        stage = "Fruiting"
        next_stage = "Harvest"
        days_to_next = 111 - effective_days
    else:
        stage = "Harvest"
        next_stage = "Completed"
        days_to_next = 0

    return {
        "current_stage": stage,
        "next_stage": next_stage,
        "days_to_next_stage": max(0, days_to_next),
        "growth_delay_days": stress_days,
    }


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/soil", methods=["POST"])
def ingest_soil_data():
    payload = request.get_json(silent=True) or {}

    if "moisture" not in payload:
        return jsonify({"error": "'moisture' field is required"}), 400

    moisture_input = payload["moisture"]
    unit = str(payload.get("unit", "percent")).lower()
    temperature = payload.get("temperature")
    humidity = payload.get("humidity")

    try:
        if unit == "raw":
            moisture_percent = analog_to_percent(moisture_input)
        else:
            moisture_percent = max(0.0, min(float(moisture_input), 100.0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid moisture value"}), 400

    now = datetime.utcnow().isoformat(timespec="seconds")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO sensor_data (moisture, temperature, humidity, captured_at) VALUES (?, ?, ?, ?)",
        (moisture_percent, temperature, humidity, now),
    )
    conn.commit()
    conn.close()

    return (
        jsonify({"message": "Data saved", "captured_at": now, "moisture_percent": moisture_percent}),
        201,
    )


@app.route("/api/data")
def get_data():
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(limit, 500))

    conn = get_db_connection()
    rows = conn.execute(
        "SELECT moisture, temperature, humidity, captured_at FROM sensor_data ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    data = [dict(row) for row in reversed(rows)]
    for item in data:
        item["moisture_percent"] = round(float(item["moisture"]), 2)

    return jsonify({"count": len(data), "data": data})


@app.route("/api/planting-date", methods=["POST"])
def save_planting_date():
    payload = request.get_json(silent=True) or {}
    planting_date = payload.get("planting_date")

    if not planting_date:
        return jsonify({"error": "'planting_date' is required in YYYY-MM-DD format"}), 400

    try:
        datetime.strptime(planting_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO crop_config (id, planting_date) VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET planting_date = excluded.planting_date
        """,
        (planting_date,),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Planting date saved: {planting_date}"})


@app.route("/api/prediction")
def get_prediction():
    conn = get_db_connection()
    planting_date = get_planting_date(conn)
    moisture_rows = conn.execute("SELECT moisture FROM sensor_data ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()

    if not planting_date:
        return jsonify(
            {
                "current_stage": "Unknown",
                "next_stage": "Unknown",
                "days_to_next_stage": None,
                "message": "Set planting date first",
            }
        )

    days_since_planting = (datetime.utcnow().date() - planting_date).days
    avg_moisture = mean([float(row["moisture"]) for row in moisture_rows]) if moisture_rows else 50.0

    prediction = predict_lifecycle(days_since_planting, avg_moisture)
    prediction["days_since_planting"] = max(0, days_since_planting)
    prediction["avg_moisture_last_30"] = round(avg_moisture, 2)
    prediction["planting_date"] = planting_date.isoformat()

    return jsonify(prediction)


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
