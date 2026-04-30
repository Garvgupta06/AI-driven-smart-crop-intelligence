from flask import Flask, render_template, jsonify, redirect, request, session, url_for
from datetime import date, timedelta
import os
import sqlite3
import warnings
import joblib
import numpy as np
import requests
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

def load_env_file(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env_file()

BLYNK_TOKEN = os.getenv("BLYNK_TOKEN", "")
DATABASE = "irrigation.db"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
MODEL_DIR = "model"

warnings.filterwarnings("ignore", category=UserWarning)

IRRIGATION_MODEL = joblib.load(os.path.join(MODEL_DIR, "irrigation_model_optimized.pkl"))
IRRIGATION_MODEL.n_jobs = 1
IRRIGATION_SCALER = joblib.load(os.path.join(MODEL_DIR, "irrigation_scaler_optimized.pkl"))
IRRIGATION_SELECTOR = joblib.load(os.path.join(MODEL_DIR, "irrigation_selector_optimized.pkl"))
CROP_ENCODER = joblib.load(os.path.join(MODEL_DIR, "irrigation_crop_encoder_optimized.pkl"))
SEASON_ENCODER = joblib.load(os.path.join(MODEL_DIR, "irrigation_season_encoder_optimized.pkl"))
REGION_ENCODER = joblib.load(os.path.join(MODEL_DIR, "irrigation_region_encoder_optimized.pkl"))

CROP_OPTIONS = list(CROP_ENCODER.categories_[0])
SEASON_OPTIONS = list(SEASON_ENCODER.classes_)
REGION_OPTIONS = list(REGION_ENCODER.classes_)
GROWTH_STAGE_OPTIONS = ["Sowing", "Vegetative", "Flowering", "Fruiting", "Harvest"]
DEFAULT_PREDICTION_SETTINGS = {
    "crop_type": "Cotton",
    "season": "Kharif",
    "region": "Central",
    "crop_growth_stage": "Sowing",
    "days_since_rain": "5",
    "field_area": "2",
}

FULL_FEATURE_ORDER = [
    "Humidity", "Soil_Moisture", "Temperature_C", "extreme_heat", "heat_stress",
    "cold_stress", "optimal_temp", "severe_drought", "moisture_stress",
    "moisture_stress_squared", "optimal_moisture", "low_humidity", "high_humidity",
    "humidity_stress", "et_factor", "water_deficit", "irrigation_urgency",
    "total_stress", "comfort_score", "water_supply_demand", "humidity_temp_ratio",
    "temp_squared", "moisture_squared", "temp_moisture_interaction",
    "season_water_need", "crop_water_need", "region_stress", "days_since_rain",
    "growth_stage_need", "field_size_cat", "Season_encoded", "Region_encoded",
    "Crop_Maize", "Crop_Potato", "Crop_Rice", "Crop_Sugarcane", "Crop_Wheat"
]


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)

    user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (DEFAULT_USERNAME,)
    ).fetchone()

    if user is None:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (DEFAULT_USERNAME, generate_password_hash(DEFAULT_PASSWORD))
        )

    conn.commit()
    conn.close()


init_db()


def fetch_blynk_data():
    url = f"https://blynk.cloud/external/api/get?token={BLYNK_TOKEN}&V0&V1&V2"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res.json()


def get_prediction_settings(source=None):
    settings = DEFAULT_PREDICTION_SETTINGS.copy()
    settings.update(session.get("prediction_settings", {}))

    last_rain_date = settings.get("last_rain_date")
    if last_rain_date:
        try:
            rain_date = date.fromisoformat(last_rain_date)
            settings["days_since_rain"] = str(max(0, (date.today() - rain_date).days))
        except ValueError:
            settings.pop("last_rain_date", None)

    if source:
        for key in DEFAULT_PREDICTION_SETTINGS:
            value = source.get(key)
            if value:
                settings[key] = value

    return settings


def save_prediction_settings(source):
    settings = get_prediction_settings(source)
    days_since_rain = source.get("days_since_rain")

    if days_since_rain:
        settings["last_rain_date"] = (
            date.today() - timedelta(days=int(days_since_rain))
        ).isoformat()

    session["prediction_settings"] = settings
    return settings


def sensor_data_to_prediction_values(sensor_data):
    return {
        "soil_moisture": sensor_data.get("V0", 35),
        "temperature": sensor_data.get("V1", 30),
        "humidity": sensor_data.get("V2", 55),
    }


def predict_irrigation(form_data):
    humidity = float(form_data["humidity"])
    soil_moisture = float(form_data["soil_moisture"])
    temperature = float(form_data["temperature"])
    crop_type = form_data["crop_type"]
    season = form_data["season"]
    region = form_data["region"]
    crop_growth_stage = form_data["crop_growth_stage"]
    days_since_rain = int(form_data["days_since_rain"])
    field_area = float(form_data["field_area"])

    # Use ML model probability threshold for irrigation decision
    IRRIGATION_THRESHOLD = 0.5  # Change this value if you want a different threshold

    temp = temperature
    extreme_heat = int(temp > 40)
    heat_stress = max(0, temp - 35) / 10
    cold_stress = max(0, 20 - temp) / 20
    optimal_temp = int(20 <= temp <= 30)

    severe_drought = int(soil_moisture < 20)
    moisture_stress = max(0, 40 - soil_moisture) / 40
    moisture_stress_squared = moisture_stress ** 2
    optimal_moisture = int(40 <= soil_moisture <= 70)

    low_humidity = int(humidity < 40)
    high_humidity = int(humidity > 80)
    humidity_stress = abs(humidity - 60) / 60

    et_factor = temp * (1 - humidity / 100) * max(0, 1 - soil_moisture / 100)
    water_deficit = max(0, (temp / 25) * (1 - humidity / 100) - soil_moisture / 100)
    irrigation_urgency = water_deficit * (1 + heat_stress)
    total_stress = (heat_stress + moisture_stress + humidity_stress) / 3
    comfort_score = (optimal_temp + optimal_moisture + int(50 <= humidity <= 70)) / 3

    water_supply_demand = soil_moisture / (temp + 1)
    humidity_temp_ratio = humidity / (temp + 1)
    temp_squared = temp ** 2
    moisture_squared = soil_moisture ** 2
    temp_moisture_interaction = temp * soil_moisture / 1000

    season_water_need_map = {"Kharif": 3, "Rabi": 2, "Zaid": 1}
    crop_water_need_map = {"Rice": 4, "Sugarcane": 4, "Cotton": 3, "Maize": 2, "Wheat": 2, "Potato": 1}
    region_stress_map = {"West": 3, "South": 2, "Central": 2, "North": 1, "East": 1}
    growth_stage_need_map = {"Sowing": 2, "Vegetative": 3, "Flowering": 4, "Fruiting": 3, "Harvest": 1}

    crop_encoded = CROP_ENCODER.transform([[crop_type]])[0]
    crop_columns = [f"Crop_{cat}" for cat in CROP_ENCODER.categories_[0][1:]]

    feature_dict = {
        "Humidity": humidity,
        "Soil_Moisture": soil_moisture,
        "Temperature_C": temp,
        "extreme_heat": extreme_heat,
        "heat_stress": heat_stress,
        "cold_stress": cold_stress,
        "optimal_temp": optimal_temp,
        "severe_drought": severe_drought,
        "moisture_stress": moisture_stress,
        "moisture_stress_squared": moisture_stress_squared,
        "optimal_moisture": optimal_moisture,
        "low_humidity": low_humidity,
        "high_humidity": high_humidity,
        "humidity_stress": humidity_stress,
        "et_factor": et_factor,
        "water_deficit": water_deficit,
        "irrigation_urgency": irrigation_urgency,
        "total_stress": total_stress,
        "comfort_score": comfort_score,
        "water_supply_demand": water_supply_demand,
        "humidity_temp_ratio": humidity_temp_ratio,
        "temp_squared": temp_squared,
        "moisture_squared": moisture_squared,
        "temp_moisture_interaction": temp_moisture_interaction,
        "season_water_need": season_water_need_map[season],
        "crop_water_need": crop_water_need_map[crop_type],
        "region_stress": region_stress_map[region],
        "days_since_rain": days_since_rain,
        "growth_stage_need": growth_stage_need_map[crop_growth_stage],
        "field_size_cat": 1 if field_area <= 2 else 2 if field_area <= 8 else 3,
        "Season_encoded": SEASON_ENCODER.transform([season])[0],
        "Region_encoded": REGION_ENCODER.transform([region])[0],
    }

    for index, column in enumerate(crop_columns):
        feature_dict[column] = crop_encoded[index]

    feature_array = np.array([[feature_dict[column] for column in FULL_FEATURE_ORDER]])
    selected_features = IRRIGATION_SELECTOR.transform(feature_array)
    scaled_features = IRRIGATION_SCALER.transform(selected_features)

    irrigation_probability = float(IRRIGATION_MODEL.predict_proba(scaled_features)[0][1])
    prediction = 1 if irrigation_probability >= IRRIGATION_THRESHOLD else 0

    risk_analysis = {
        "temperature_stress": "High" if heat_stress > 0.2 else "Low",
        "moisture_stress": "High" if moisture_stress > 0.3 else "Low",
        "overall_stress": "High" if total_stress > 0.4 else "Medium" if total_stress > 0.2 else "Low",
        "crop_water_demand": "High" if feature_dict["crop_water_need"] >= 3 else "Medium" if feature_dict["crop_water_need"] >= 2 else "Low",
        "irrigation_urgency": f"{irrigation_urgency:.2f}",
        "optimal_conditions": "Yes" if comfort_score > 0.6 else "No",
    }

    return {
        "prediction": "IRRIGATION NEEDED" if prediction else "NO IRRIGATION NEEDED",
        "irrigation_probability": round(irrigation_probability * 100, 2),
        "risk_analysis": risk_analysis,
    }


def prediction_context(result=None, error=None, form_values=None):
    return {
        "crop_options": CROP_OPTIONS,
        "season_options": SEASON_OPTIONS,
        "region_options": REGION_OPTIONS,
        "growth_stage_options": GROWTH_STAGE_OPTIONS,
        "result": result,
        "error": error,
        "form_values": form_values or get_prediction_settings(),
    }

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html", error=None)

    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], password):
        session['logged_in'] = True
        session['username'] = user["username"]
        return redirect(url_for('dashbord'))

    return render_template("login.html", error="Invalid username or password")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/data')
def get_data():
    if not session.get('logged_in'):
        return jsonify({"error": "Login required"}), 401

    try:
        return jsonify(fetch_blynk_data())
    except:
        return jsonify({"error": "Failed to fetch data"})

@app.route('/dashbord')
def dashbord():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    return render_template('dashbord.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template("predict.html", **prediction_context())

    try:
        save_prediction_settings(request.form)
        result = predict_irrigation(request.form)
        return render_template(
            "predict.html",
            **prediction_context(result=result, form_values=request.form)
        )
    except Exception as exc:
        return render_template(
            "predict.html",
            **prediction_context(error=f"Prediction failed: {exc}", form_values=request.form)
        )

@app.route('/predict-json', methods=['POST'])
def predict_json():
    if not session.get('logged_in'):
        return jsonify({"error": "Login required"}), 401

    try:
        form_data = request.get_json(silent=True) or request.form
        settings = save_prediction_settings(form_data)
        prediction_data = dict(settings)
        prediction_data.update({
            "soil_moisture": form_data.get("soil_moisture", 35),
            "temperature": form_data.get("temperature", 30),
            "humidity": form_data.get("humidity", 55),
        })
        return jsonify(predict_irrigation(prediction_data))
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 400

@app.route('/auto-predict')
def auto_predict():
    if not session.get('logged_in'):
        return jsonify({"error": "Login required"}), 401

    try:
        sensor_data = fetch_blynk_data()
        prediction_data = get_prediction_settings()
        prediction_data.update(sensor_data_to_prediction_values(sensor_data))
        result = predict_irrigation(prediction_data)
        result["sensor_data"] = sensor_data
        result["settings"] = prediction_data
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Auto prediction failed: {exc}"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

