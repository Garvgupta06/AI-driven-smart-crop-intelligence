# AI-driven-smart-crop-intelligence

# Updates

## Version 0.1 (March 2026)

### What is included in v0.1
- Initial ESP32-based smart crop monitoring setup
- Soil moisture, temperature, and humidity data collection
- Basic rain and light sensing integration
- Flask web dashboard foundation for live monitoring
- Manual and automatic irrigation control logic (base implementation)

### Current status
- Prototype phase completed
- Hardware + web dashboard integration is in progress
- Next step: improve automation logic and deploy stable dashboard

### ML Model v0.1

Binary classification model to predict whether irrigation is needed based on IoT sensor data and manual inputs.

**Dataset:** `irrigation_prediction.csv`

**Target Variable:**
- 0 = No Irrigation Needed (Low demand)
- 1 = Irrigation Needed (Medium/High demand)

**Features Used:**

| Type | Features |
|------|----------|
| Sensor Inputs | Humidity, Soil_Moisture, Temperature_C |
| Manual Inputs | Crop_Type, Season, Region |
| Engineered | temp_humidity, temp_moisture |

**Encoding:**
- Crop_Type: One-Hot Encoded (Wheat, Rice, Cotton, Maize, Sugarcane, Potato)
- Season: Label Encoded (Kharif: 0, Rabi: 1, Zaid: 2)
- Region: Label Encoded (Central: 0, East: 1, North: 2, South: 3, West: 4)

**Model Accuracies:**
| Model | Accuracy |
|-------|----------|
| Random Forest Classifier | ~70% |
| XGBoost Classifier | ~70% |

**PKL Files Generated:**
| File | Description |
|------|-------------|
| `irrigation_model.pkl` | Trained Random Forest model |
| `irrigation_feature_names.pkl` | List of feature column names in training order |
| `irrigation_crop_encoder.pkl` | OneHotEncoder for Crop_Type |
| `irrigation_season_encoder.pkl` | LabelEncoder for Season |
| `irrigation_region_encoder.pkl` | LabelEncoder for Region |

**Prediction Function:**
```python
predict_irrigation(humidity, soil_moisture, temperature, crop_type, season, region)
# Returns: (prediction, probability)
# prediction: 0 or 1
# probability: confidence score (0.0 - 1.0)
```

## Project Objectives
- Detect Soil Moisture
- Monitor temperature and humidity
- Toggle automatic irrigation (on/off)
- Live web dashboard with graphs
- Manual control and automation control

## Hardware Requirements
### Microcontroller:
- ESP32

### Sensors:
- Soil moisture sensor
- DHT11 or DHT22
- LDR
- Rain Sensor
- 5V Adapter
- 12V Adapter
- Voltage Regulator

## Software Requirements:
- Core framework
- Flask
- Flask-CORS
- Flask-RESTful
- Flask-JWT-Extended
- Werkzeug
- MongoDB

## Flask Workflow
1. ESP32 collects sensor values (soil moisture, temperature, humidity, rain, light).
2. Device sends data to Flask backend API endpoints.
3. Flask validates and processes incoming payloads.
4. Processed data is stored in MongoDB for history and analysis.
5. Frontend dashboard requests latest and historical data from Flask APIs.
6. Dashboard updates charts and status cards in near real-time.
7. User actions (manual motor ON/OFF or mode switch) are sent to Flask.
8. Flask forwards control decisions to the irrigation logic/device layer.

### Flask App Structure (v0.1)
- `Website/app.py`: main Flask application entry point
- `Website/templates/index.html`: dashboard template
- `Website/static/js/dashboard.js`: frontend API calls and chart updates
- `Website/static/css/style.css`: dashboard styling


## Design Link
- https://www.tinkercad.com/things/fhN11jeuz2I/editel?returnTo=%2Fdashboard&sharecode=qL12FBooymbpJ4HXtfxJrVG13U5Xz-ItZWC-hXHdLmU
