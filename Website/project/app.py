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
SCALER_PATH = '../../model/irrigation_scaler_optimized.pkl'
SELECTOR_PATH = '../../model/irrigation_selector_optimized.pkl'
FEATURE_NAMES_PATH = '../../model/irrigation_feature_names_optimized.pkl'

model = joblib.load(MODEL_PATH)
crop_encoder = joblib.load(CROP_ENCODER_PATH)
season_encoder = joblib.load(SEASON_ENCODER_PATH)
scaler = joblib.load(SCALER_PATH)
selector = joblib.load(SELECTOR_PATH)
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
        return {"V0": 0, "V1": 19, "V2": 55}  # fallback for demo

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
        soil_val = form_values.get('soil_moisture', sensor_data.get('V0'))
        temp_val = form_values.get('temperature', sensor_data.get('V1'))
        hum_val = form_values.get('humidity', sensor_data.get('V2'))
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
        # Encode categorical
        crop_encoded = crop_encoder.transform([[crop]])[0]
        season_encoded = season_encoder.transform([[season]])[0]
        # For region and growth stage, use label encoding manually (since you may not have .pkl for these)
        region_map = {"North": 0, "South": 1, "East": 2, "West": 3, "Central": 4}
        growth_stage_map = {"Sowing": 0, "Vegetative": 1, "Flowering": 2, "Fruiting": 3, "Harvest": 4}
        region_encoded = region_map.get(region, 0)
        growth_stage_encoded = growth_stage_map.get(growth_stage, 0)
        # Prepare feature array (add region and growth stage)
        features = [soil, temp, hum]
        features += crop_encoded.tolist()  # flatten one-hot
        features.append(season_encoded if np.isscalar(season_encoded) else season_encoded[0])
        features.append(region_encoded)
        features.append(growth_stage_encoded)
        # Build full feature vector in model's expected order
        feature_dict = {}
        # Fill with defaults first
        for fname in feature_names:
            feature_dict[fname] = 0
        # Update with real values from form/sensor
        feature_dict['Soil_Moisture'] = float(soil_val)
        feature_dict['Temperature_C'] = float(temp_val)
        feature_dict['Humidity'] = float(hum_val)
        # For categorical features, use encoders
        feature_dict['Crop_Type'] = crop  # will be handled by encoder
        feature_dict['Season'] = season   # will be handled by encoder
        feature_dict['Region'] = region   # will be handled by encoder
        feature_dict['Crop_Growth_Stage'] = growth_stage  # will be handled by encoder
        # If you have one-hot encoded features, you must expand them using your encoder
        # For example, if crop_encoder is a OneHotEncoder:
        crop_onehot = crop_encoder.transform([[crop]])[0]
        for i, cname in enumerate(crop_encoder.get_feature_names_out(['Crop_Type'])):
            feature_dict[cname] = crop_onehot[i]
        # Repeat for other categorical encoders as needed
        # Build the input vector in the correct order
        input_vector = [feature_dict[f] for f in feature_names]
        X = np.array([input_vector])
        X_scaled = scaler.transform(X)
        X_selected = selector.transform(X_scaled)
        pred = model.predict(X_selected)[0]
        prediction_result = "Irrigation Needed" if pred == 1 else "No Irrigation Needed"
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

warnings.filterwarnings("ignore", category=UserWarning,debug=True)
