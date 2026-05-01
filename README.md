# Smart Irrigation — Pipeline Overview

This repository implements an end-to-end smart-irrigation pipeline: ESP32 field sensors → Flask web dashboard → ML pipeline (feature engineering → selection → scaler → model) → prediction results shown to the user. The README below explains the production inference pipeline used by the web app, the training artefacts, and how to run and debug the system locally.

**Key goals:** reliable irrigation suggestions from live sensor data, transparent feature pipeline, and a small, reproducible inference surface used by the Flask app.

**Note:** Do not store secrets (API tokens) in source code. Set them via environment variables or a config file in production.

**Relevant paths** (workspace root):
- `Website/project/app.py` — Flask application (serves UI, `/data` and `/predict`).
- `Website/project/test_pipeline.py` — small script to validate pipeline artifacts locally.
- `Website/project/templates/` and `Website/project/static/` — frontend templates and JS/CSS.
- `model/` — saved model artifacts and notebook (`irrigation_model_optimized.ipynb`).

**Primary model artifacts in `model/`:**
- `irrigation_model_optimized.pkl` — trained RandomForest model used in production.
- `irrigation_scaler_optimized.pkl` — StandardScaler fitted on the final (selected) features.
- `irrigation_crop_encoder_optimized.pkl` — OneHotEncoder for crop types.
- `irrigation_season_encoder_optimized.pkl` — encoder for seasons.
- `irrigation_region_encoder_optimized.pkl` — encoder for regions.
- `irrigation_feature_names_optimized.pkl` — ordered list of the selected (top-20) features used for inference.

## Training vs Inference (short)
- Training pipeline (in `model/irrigation_model_optimized.ipynb`) builds ~37 engineered features (stress indicators, interactions, polynomial terms and domain-mapped features), then uses `SelectKBest` to pick the top 20 features. The scaler is fitted on those selected 20 features and the RandomForest model trained on the scaled selection.
- Inference (production) must use the exact same feature calculations and the same 20 feature ordering saved in `irrigation_feature_names_optimized.pkl`. The Flask app reconstructs engineered features, fills a dictionary of candidate features, then builds an input vector using only these saved top-20 names, scales that vector with the saved scaler, and calls `model.predict()`.

## Inference pipeline (what `app.py` does)
1. Read sensor and form values (soil moisture, temperature, humidity, crop, season, region, growth stage, days since rain, field area).
2. Compute engineered numeric features exactly as in training (examples include `heat_stress`, `moisture_stress`, `et_factor`, `water_deficit`, `temp_squared`, `growth_stage_need`, etc.).
3. Use saved encoders to transform categorical variables (crop one-hot expansion, season/region encoding) using the same naming convention the training notebook used.
4. Build an ordered vector using `irrigation_feature_names_optimized.pkl` (the saved top-20 list).
5. Scale the vector with `irrigation_scaler_optimized.pkl`.
6. Call `irrigation_model_optimized.pkl`'s `predict()` (and optionally `predict_proba()` for confidence).

Important: Do not run feature-selection (`SelectKBest`) at inference time — the model expects exactly the selected 20 features in the same order that the scaler and model were trained on. The repository's `app.py` has been updated to follow this rule.

## Web app flow
- Frontend (`static/script.js`) polls `/data` every few seconds to get sensor pins from Blynk (via backend `/data`).
- The prediction page contains hidden inputs that are updated from live sensor values; when the user submits `/predict` the server computes the engineered features and runs inference.
- API endpoints in `app.py` to note:
    - `GET /` and `GET /home` — homepage
    - `GET /dashbord` — dashboard (requires login)
    - `GET|POST /predict` — manual prediction page and form handler
    - `GET /data` — returns latest Blynk values (V0,V1,V2)

## Hardware & Sensors
This project integrates an ESP32-based field node and a small set of common agricultural sensors and actuators. The list below describes what was used during development and practical notes for integration.

- Microcontroller: **ESP32** (Wi-Fi enabled, low-power MCU)
- Sensors:
    - **Soil moisture sensor (capacitive)** — measures volumetric water content; preferred over resistive probes for longevity.
    - **Temperature + Humidity sensor (DHT11 / DHT22)** — environmental readings used to compute stress features.
    - **Rain sensor** — used to estimate recent rainfall for `days_since_rain` and rain-based logic.
    - **Light sensor (LDR)** — optional, used for daylight-aware automation.
    - **Optional:** flow sensors / pressure sensors can be added for advanced irrigation telemetry.
- Actuators & power:
    - **Relay modules** or **MOSFET/transistor drivers** to switch pumps or solenoid valves safely.
    - **Solenoid valve / water pump** — actual irrigation actuator connected through a relay or driver.
    - **Power:** 5V logic supply for sensors and ESP32; 12V (or appropriate) supply for pumps/valves with proper regulation.

Integration notes:
- Use the ESP32 ADC carefully: add proper voltage dividers and calibration for analog soil sensors and avoid driving sensors above 3.3V.
- Use opto-isolation or driver circuits for relays and include flyback diodes across inductive loads (valves, pumps).
- Place sensors where they represent field conditions (soil probe depth, shaded vs exposed areas) and consider multiple probes if the field is heterogeneous.
- Debounce and low-pass filter fast-changing sensor readings on the device or backend before passing values to the ML pipeline.

These hardware choices align with the features engineered in the model notebook (soil moisture, temperature, humidity, and derived stress/interaction features). If you want, I can add a wiring diagram and a minimal ESP32 sketch to stream data to Blynk or the Flask backend.

## How to run locally
1. Create and activate a virtual environment (Windows example):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r requirement.txt
```
3. (Optional) Test pipeline artifacts without running server:
```powershell
python Website/project/test_pipeline.py
```
This script prints feature names, attempts a Blynk fetch (if token present in `app.py`), and runs a couple of sample cases through the saved scaler + model to validate shapes.
4. Run the Flask app (from `Website/project`):
```powershell
python app.py
```
Then open `http://localhost:5000/`.

## Troubleshooting — common issues
- Soil shows `0` in the UI and predictions are unexpected:
    - Check Blynk fetch: confirm token is configured securely (do not commit it). If the backend cannot reach Blynk it should not silently return a 0; inspect logs from `fetch_blynk_data()` and update token.
    - Confirm `irrigation_feature_names_optimized.pkl` is present and up-to-date. Mismatched feature ordering causes incorrect model inputs.
- Prediction returns 500 Internal Server Error:
    - Look at the Flask server console for the Python traceback. Common causes: missing model files, wrong feature names, or None values where floats expected. The repo includes `test_pipeline.py` to reproduce these problems locally.
- Frontend auto-prediction fails:
    - `static/script.js` attempts JSON auto-prediction endpoints (`/predict-json` or `/auto-predict`) but these are not implemented by default. Manual `/predict` (form POST) is implemented and recommended for testing.

## Development notes & next steps
- Replace hard-coded tokens with environment variables or a small config loader.
- Add a JSON auto-predict endpoint that returns model probability and risk analysis for the frontend UI.
- Add unit tests that exercise the feature engineering functions and ensure the `input_vector` built in `app.py` matches `irrigation_feature_names_optimized.pkl` ordering.

