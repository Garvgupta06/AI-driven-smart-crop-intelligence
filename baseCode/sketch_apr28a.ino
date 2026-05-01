#define BLYNK_TEMPLATE_ID "TMPL3SETXa3yQ"
#define BLYNK_TEMPLATE_NAME "SoilSystem"
#define BLYNK_AUTH_TOKEN "rDOZLu0KXsRmLaf7MIQd_H1Sg2TQO3-h"

#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>
#include <DHT.h>

char ssid[] = "Garv Gupta";
char pass[] = "csp2zczh";

#define SOIL_PIN A0
#define DHTPIN D2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
BlynkTimer timer;

// 🔁 Sensor read + send
void sendData() {

  int soilRaw = analogRead(SOIL_PIN);
  int soil = map(soilRaw, 1023, 400, 0, 100);

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  // ❌ Sensor error check
  if (isnan(temp) || isnan(hum)) {
    Serial.println("❌ DHT Error - Data Not Sent");
    return;
  }

  // ✅ Check Blynk connection
  if (Blynk.connected()) {

    Blynk.virtualWrite(V0, soil);
    Blynk.virtualWrite(V1, temp);
    Blynk.virtualWrite(V2, hum);

    Serial.println("✅ Data Sent to Blynk");

  } else {
    Serial.println("❌ Not Sent (Blynk Disconnected)");
  }

  // 📊 Debug values
  Serial.println("------ Sensor Data ------");

  Serial.print("Soil: ");
  Serial.println(soil);

  Serial.print("Temperature: ");
  Serial.println(temp);

  Serial.print("Humidity: ");
  Serial.println(hum);

  Serial.println("-------------------------\n");
}

void setup() {
  Serial.begin(9600);
  dht.begin();

  Serial.print("Connecting to WiFi");

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);

  if (Blynk.connected()) {
    Serial.println("\n✅ Blynk Connected");
  } else {
    Serial.println("\n❌ Blynk Not Connected");
  }

  timer.setInterval(2000L, sendData);  // every 2 sec
}

void loop() {
  Blynk.run();
  timer.run();
}
