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
