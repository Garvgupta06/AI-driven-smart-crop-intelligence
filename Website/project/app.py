# ------------------- Imports & App Setup -------------------
from flask import Flask, render_template, jsonify, redirect, request, session, url_for
import warnings
import requests
import joblib
import numpy as np

# Load model and preprocessors once at startup
MODEL_PATH = '../../model/irrigation_model_optimized.pkl'
CROP_ENCODER_PATH = '../../model/irrigation_crop_encoder_optimized.pkl'
SEASON_ENCODER_PATH = '../../model/irrigation_season_encoder_optimized.pkl'
REGION_ENCODER_PATH = '../../model/irrigation_region_encoder_optimized.pkl'
SCALER_PATH = '../../model/irrigation_scaler_optimized.pkl'
FEATURE_NAMES_PATH = '../../model/irrigation_feature_names_optimized.pkl'

model = joblib.load(MODEL_PATH)
crop_encoder = joblib.load(CROP_ENCODER_PATH)
season_encoder = joblib.load(SEASON_ENCODER_PATH)
region_encoder = joblib.load(REGION_ENCODER_PATH)
scaler = joblib.load(SCALER_PATH)
feature_names = joblib.load(FEATURE_NAMES_PATH)

BLYNK_TOKEN = "rDOZLu0KXsRmLaf7MIQd_H1Sg2TQO3-h"
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

def fetch_blynk_data():
    url = f"https://blynk.cloud/external/api/get?token={BLYNK_TOKEN}&V0&V1&V2"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        # Log and return None values so caller can detect failures
        print(f"Blynk fetch failed: {e}")
        return {"V0": None, "V1": None, "V2": None}

# Home page
@app.route("/home")
@app.route("/")
def home():
    return render_template("index.html")

# About page
@app.route("/about")
def about():
    return render_template("about.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Simple demo login (replace with real logic)
        if username == "admin" and password == "admin":
            session["user"] = username
            return redirect(url_for("dashbord"))
        else:
            error = "Invalid credentials. Please try admin/admin."
    return render_template("login.html", error=error)

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# Dashboard page
@app.route("/dashbord")
def dashbord():
    if not session.get("user"):
        return redirect(url_for("login"))
    data = fetch_blynk_data()
    return render_template("dashbord.html", data=data)

# Prediction page
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if not session.get("user"):
        return redirect(url_for("login"))
    crop_options = ["Wheat", "Rice", "Maize", "Sugarcane", "Cotton", "Potato"]
    season_options = ["Kharif", "Rabi", "Zaid"]
    region_options = ["North", "South", "East", "West", "Central"]
    growth_stage_options = ["Sowing", "Vegetative", "Flowering", "Fruiting", "Harvest"]
    # Always provide form_values for GET and POST
    form_values = {}
    prediction_result = None
    alert_message = None
    if request.method == "POST":
        form_values = request.form.to_dict()
        # Get sensor data as fallback
        sensor_data = fetch_blynk_data()
        soil_val = form_values.get('soil_moisture') if form_values.get('soil_moisture') not in (None, '') else sensor_data.get('V0')
        temp_val = form_values.get('temperature') if form_values.get('temperature') not in (None, '') else sensor_data.get('V1')
        hum_val = form_values.get('humidity') if form_values.get('humidity') not in (None, '') else sensor_data.get('V2')
        days_since_rain_val = form_values.get('days_since_rain', None)
        field_area_val = form_values.get('field_area', None)
        region = form_values.get('region', 'North')
        growth_stage = form_values.get('crop_growth_stage', 'Sowing')
        alert_message = None
        if soil_val is None or temp_val is None or hum_val is None:
            alert_message = "Sensor and form data missing or invalid! Please check your sensors or input."
            # Set fallback values to avoid crash
            soil = 35
            temp = 30
            hum = 55
        else:
            soil = float(soil_val)
            temp = float(temp_val)
            hum = float(hum_val)
        crop = form_values.get('crop_type', 'Wheat')
        season = form_values.get('season', 'Kharif')
        days_since_rain = int(days_since_rain_val) if days_since_rain_val not in (None, '') else 5
        field_area = float(field_area_val) if field_area_val not in (None, '') else 2.0
        # Build the full engineered feature vector matching training pipeline
        # base numeric values (use validated fallback-safe vars)
        soil_moisture = float(soil)
        temp_c = float(temp)
        humidity = float(hum)

        # Stress features
        extreme_heat = 1 if temp_c > 40 else 0
        heat_stress = max(0.0, temp_c - 35) / 10.0
        cold_stress = max(0.0, 20 - temp_c) / 20.0
        optimal_temp = 1 if 20 <= temp_c <= 30 else 0
        severe_drought = 1 if soil_moisture < 20 else 0
        moisture_stress = max(0.0, 40 - soil_moisture) / 40.0
        moisture_stress_squared = moisture_stress ** 2
        optimal_moisture = 1 if 40 <= soil_moisture <= 70 else 0
        low_humidity = 1 if humidity < 40 else 0
        high_humidity = 1 if humidity > 80 else 0
        humidity_stress = abs(humidity - 60) / 60.0

        # Interaction / domain features
        et_factor = temp_c * (1 - humidity / 100.0) * max(0.0, 1 - soil_moisture / 100.0)
        water_deficit = max(0.0, (temp_c / 25.0) * (1 - humidity / 100.0) - soil_moisture / 100.0)
        irrigation_urgency = water_deficit * (1 + heat_stress)
        total_stress = (heat_stress + moisture_stress + humidity_stress) / 3.0
        comfort_score = (optimal_temp + optimal_moisture + (1 if 50 <= humidity <= 70 else 0)) / 3.0
        water_supply_demand = soil_moisture / (temp_c + 1.0)
        humidity_temp_ratio = humidity / (temp_c + 1.0)

        # Polynomial
        temp_squared = temp_c ** 2
        moisture_squared = soil_moisture ** 2
        temp_moisture_interaction = temp_c * soil_moisture / 1000.0

        # Domain mappings
        season_water_need_map = {"Kharif": 3, "Rabi": 2, "Zaid": 1}
        season_water_need = season_water_need_map.get(season, 2)
        crop_water_need_map = {"Rice": 4, "Sugarcane": 4, "Cotton": 3, "Maize": 2, "Wheat": 2, "Potato": 1}
        crop_water_need = crop_water_need_map.get(crop, 2)
        region_stress_map = {"West": 3, "South": 2, "Central": 2, "North": 1, "East": 1}
        region_stress = region_stress_map.get(region, 1)
        # days_since_rain and field_area we got earlier

        growth_stage_need_map = {"Sowing": 2, "Vegetative": 3, "Flowering": 4, "Fruiting": 3, "Harvest": 1}
        growth_stage_need = growth_stage_need_map.get(growth_stage, 2)
        # field size category (1,2,3)
        if field_area <= 2:
            field_size_cat = 1
        elif field_area <= 8:
            field_size_cat = 2
        else:
            field_size_cat = 3

        # One-hot encode crop using the same training naming convention
        try:
            crop_onehot = np.asarray(crop_encoder.transform([[crop]])[0], dtype=float)
            # Training notebook used: crop_columns = [f'Crop_{cat}' for cat in categories_[0][1:]]
            crop_columns = [f"Crop_{cat}" for cat in crop_encoder.categories_[0][1:]]
        except Exception:
            # fallback simple mapping
            crop_onehot = np.array([], dtype=float)
            crop_columns = []

        # Season & region encoded
        try:
            season_encoded = season_encoder.transform([season])[0]
        except Exception:
            season_encoded = 0
        try:
            region_encoded = region_encoder.transform([region])[0]
        except Exception:
            region_encoded = 0

        # Build candidate engineered feature dictionary.
        # Inference uses only saved top-20 selected feature names from FEATURE_NAMES_PATH.
        feature_dict = {}

        # Fill numeric engineered features
        values_map = {
            'Humidity': humidity,
            'Soil_Moisture': soil_moisture,
            'Temperature_C': temp_c,
            'extreme_heat': extreme_heat,
            'heat_stress': heat_stress,
            'cold_stress': cold_stress,
            'optimal_temp': optimal_temp,
            'severe_drought': severe_drought,
            'moisture_stress': moisture_stress,
            'moisture_stress_squared': moisture_stress_squared,
            'optimal_moisture': optimal_moisture,
            'low_humidity': low_humidity,
            'high_humidity': high_humidity,
            'humidity_stress': humidity_stress,
            'et_factor': et_factor,
            'water_deficit': water_deficit,
            'irrigation_urgency': irrigation_urgency,
            'total_stress': total_stress,
            'comfort_score': comfort_score,
            'water_supply_demand': water_supply_demand,
            'humidity_temp_ratio': humidity_temp_ratio,
            'temp_squared': temp_squared,
            'moisture_squared': moisture_squared,
            'temp_moisture_interaction': temp_moisture_interaction,
            'season_water_need': season_water_need,
            'crop_water_need': crop_water_need,
            'region_stress': region_stress,
            'days_since_rain': days_since_rain,
            'growth_stage_need': growth_stage_need,
            'field_size_cat': field_size_cat
        }
        for k, v in values_map.items():
            feature_dict[k] = float(v)

        # Add season/region encoded and crop one-hot into final dict if their names are present
        feature_dict['Season_encoded'] = float(season_encoded)
        feature_dict['Region_encoded'] = float(region_encoded)
        # Crop one-hot
        for i, cname in enumerate(crop_columns):
            if i < len(crop_onehot):
                feature_dict[cname] = float(crop_onehot[i])

        # Build ordered vector for selected top-20 features only
        input_vector = [feature_dict.get(f, 0.0) for f in feature_names]
        X = np.array([input_vector], dtype=float)
        # Debug: print vector head
        print('Input vector (first 10):', input_vector[:10])
        # Top-20 features are already selected; only scale then predict
        X_scaled = scaler.transform(X)
        pred = model.predict(X_scaled)[0]
        prob = None
        if hasattr(model, 'predict_proba'):
            prob = model.predict_proba(X_scaled)[0].tolist()
        prediction_result = "Irrigation Needed" if pred == 1 else "No Irrigation Needed"
        print('Pred:', pred, 'Prob:', prob)
    else:
        alert_message = None
    return render_template(
        "predict.html",
        crop_options=crop_options,
        season_options=season_options,
        region_options=region_options,
        growth_stage_options=growth_stage_options,
        form_values=form_values,
        prediction_result=prediction_result,
        alert_message=alert_message
    )

# Data endpoint for JS
@app.route("/data")
def data_api():
    data = fetch_blynk_data()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

warnings.filterwarnings("ignore", category=UserWarning)
