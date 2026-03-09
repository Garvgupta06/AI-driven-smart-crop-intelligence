// ESP32 sketch: read soil sensor and push data to Flask API.
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "WIFI_SSID";
const char* WIFI_PASSWORD = "WIFI_PASSWORD";
const char* SERVER_URL = "http://PC_IP:5000/api/soil";

const int SOIL_PIN = 34;     // ADC pin for ESP32
const int PUMP_PIN = 26;     // Relay or control output (optional)
const int DRY_THRESHOLD = 2500;

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void setup() {
  Serial.begin(115200);
  pinMode(SOIL_PIN, INPUT);
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW);
  connectWiFi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  int rawValue = analogRead(SOIL_PIN); // 0-4095
  Serial.print("Soil raw: ");
  Serial.println(rawValue);

  // Optional irrigation control using raw threshold.
  if (rawValue > DRY_THRESHOLD) {
    digitalWrite(PUMP_PIN, HIGH);
  } else {
    digitalWrite(PUMP_PIN, LOW);
  }

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"moisture\":" + String(rawValue) + ",\"unit\":\"raw\"}";
  int responseCode = http.POST(payload);

  Serial.print("POST status: ");
  Serial.println(responseCode);

  if (responseCode > 0) {
    String response = http.getString();
    Serial.println(response);
  }

  http.end();
  delay(15000); // send every 15 seconds
}