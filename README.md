# AI-driven-smart-crop-intelligence

## Overview

AI-powered smart agriculture system combining IoT sensors, machine learning models, and web dashboard for intelligent crop monitoring and irrigation prediction. The system integrates ESP32-based hardware with advanced ML algorithms to provide real-time agricultural insights and automated irrigation control.

## Project Objectives

- Detect soil moisture levels with precision monitoring
- Monitor temperature and humidity for environmental tracking
- Toggle automatic irrigation with manual override capabilities
- Live web dashboard with interactive graphs and data visualization
- Manual control and automation control for flexible farm management
- AI-driven irrigation decision support with 81.5% prediction accuracy

## Current Status

Version 0.2 completed with optimized ML model achieving 81.5% accuracy, representing an 11.5 percentage point improvement over baseline models. Hardware integration with ESP32-based sensor network and Flask web dashboard is in progress. Next phase focuses on production deployment and enhanced automation features.

### What is included in v0.2
- Advanced ESP32-based smart crop monitoring with optimized sensors
- Enhanced soil moisture, temperature, and humidity data collection
- Improved rain and light sensing integration with better accuracy
- Robust Flask web dashboard with real-time monitoring capabilities
- Optimized irrigation prediction model with 81.5% accuracy
- Advanced feature engineering with 27 engineered features

## Model

### Model v0.1

Binary classification model to predict whether irrigation is needed based on IoT sensor data and manual inputs. Baseline implementation using standard machine learning approaches.

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

### Model v0.2

Advanced optimization achieving 81.5% accuracy through sophisticated feature engineering and model refinement. Enhanced prediction capabilities with detailed risk analysis and improved confidence scoring.

**Key Improvements:**
- **Accuracy:** 81.5% (11.5 percentage point improvement over v0.1)
- **Cross-validation:** 83.5% ± 1.88% mean accuracy across 5-fold validation
- **Feature Engineering:** 27 advanced features including stress indicators, interaction terms, and polynomial features
- **Domain Knowledge:** Agricultural expertise integrated into feature design
- **Risk Analysis:** Comprehensive output including temperature stress, moisture stress, and crop-specific factors

**Advanced Features:**

| Type | Features |
|------|----------|
| Stress Indicators | heat_stress, cold_stress, moisture_stress, humidity_stress |
| Interaction Features | et_factor, water_deficit, irrigation_urgency, total_stress |
| Polynomial Features | temp_squared, moisture_squared, temp_moisture_interaction |
| Domain-Specific | crop_water_req, seasonal_water_need, regional_stress, growth_stage_water |
| Optimal Conditions | optimal_temp, optimal_moisture, comfort_score |

**Optimized PKL Files:**
| File | Description |
|------|-------------|
| `irrigation_model_optimized.pkl` | Optimized Random Forest model |
| `irrigation_scaler_optimized.pkl` | StandardScaler for feature normalization |
| `irrigation_selector_optimized.pkl` | SelectKBest for feature selection (20 features) |
| `irrigation_crop_encoder_optimized.pkl` | OneHotEncoder for Crop_Type |
| `irrigation_season_encoder_optimized.pkl` | LabelEncoder for Season |
| `irrigation_region_encoder_optimized.pkl` | LabelEncoder for Region |
| `irrigation_feature_names_optimized.pkl` | Selected feature names list |

**Enhanced Prediction Function:**
```python
predict_irrigation_optimized(humidity, soil_moisture, temperature, crop_type, season, region,
                           crop_growth_stage, days_since_rain, field_area)
# Returns: (prediction, confidence, risk_analysis)
# prediction: int (0=No irrigation, 1=Irrigation needed)
# confidence: float (0.0-1.0 probability score)
# risk_analysis: dict with detailed risk factors and agricultural insights
```

**Performance Metrics:**
- **Training Accuracy:** 81.5%
- **Cross-validation Mean:** 83.5% ± 1.88%
- **Feature Selection:** 20 most important features from 37 engineered features
- **Model Type:** Optimized Random Forest with hyperparameter tuning
- **Data Balancing:** SMOTE technique for handling class imbalance

## Website

Flask-based web dashboard providing real-time sensor monitoring, data visualization, and crop lifecycle tracking with RESTful API endpoints for device integration.

### Flask Workflow
1. ESP32 collects sensor values (soil moisture, temperature, humidity, rain, light).
2. Device sends data to Flask backend API endpoints.
3. Flask validates and processes incoming payloads.
4. Processed data is stored in MongoDB for history and analysis.
5. Frontend dashboard requests latest and historical data from Flask APIs.
6. Dashboard updates charts and status cards in near real-time.
7. User actions (manual motor ON/OFF or mode switch) are sent to Flask.
8. Flask forwards control decisions to the irrigation logic/device layer.

### Flask App Structure (v0.2)
- `Website/app.py`: main Flask application entry point
- `Website/templates/index.html`: dashboard template
- `Website/static/js/dashboard.js`: frontend API calls and chart updates
- `Website/static/css/style.css`: dashboard styling

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

## Design Link
- https://www.tinkercad.com/things/fhN11jeuz2I/editel?returnTo=%2Fdashboard&sharecode=qL12FBooymbpJ4HXtfxJrVG13U5Xz-ItZWC-hXHdLmU