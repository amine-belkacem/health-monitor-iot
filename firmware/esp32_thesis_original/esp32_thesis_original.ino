#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include "heartRate.h"

// Wi-Fi  (identifiants retirés avant publication)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Serveur Flask
const char* ecgUrl = "http://192.168.1.4:5000/ecg";
const char* sensorUrl = "http://192.168.1.4:5000/sensor_data";

// ECG
const int ecgPin = 34;

// DHT22
#define DHTPIN 27
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// MQ135
const int mq135Pin = 35;

// MAX30102
MAX30105 particleSensor;
#define MAX_SAMPLES 100
uint32_t irBuffer[MAX_SAMPLES];
uint32_t redBuffer[MAX_SAMPLES];
int32_t bufferLength = MAX_SAMPLES;
int32_t spo2;
int8_t validSpO2;
int32_t heartRate;
int8_t validHeartRate;

// Intervalles
unsigned long lastSensorSent = 0;
const unsigned long sensorInterval = 3000;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  Serial.print("Connexion au Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi connecté !");

  dht.begin();

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 non détecté !");
    while (1);
  }

  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x0A);
}

void loop() {
  // ECG
  int ecgValue = analogRead(ecgPin) * (3.3 / 4095.0);
  Serial.print("ECG: "); Serial.println(ecgValue);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(ecgUrl);
    http.addHeader("Content-Type", "application/json");

    String ecgPayload = "{\"ecg_value\":" + String(ecgValue) + "}";
    int httpResponseCode = http.POST(ecgPayload);

    if (httpResponseCode > 0) {
      Serial.println("ECG envoyé !");
    } else {
      Serial.print("Erreur ECG : "); Serial.println(httpResponseCode);
    }
    http.end();
  }

  delay(10);

  // Données toutes les 3 secondes
  if (millis() - lastSensorSent > sensorInterval) {
    lastSensorSent = millis();

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    int airQuality = analogRead(mq135Pin);

    // Lire 100 échantillons du capteur MAX30102
    for (int i = 0; i < bufferLength; i++) {
      while (particleSensor.available() == false);
      redBuffer[i] = particleSensor.getRed();
      irBuffer[i] = particleSensor.getIR();
      particleSensor.nextSample();
    }

    // Calcul BPM + SpO2
    maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer,
                                           &spo2, &validSpO2, &heartRate, &validHeartRate);

    if (validHeartRate && validSpO2) {
      Serial.println("Données capteurs réelles :");
      Serial.print("Température : "); Serial.println(temperature);
      Serial.print("Humidité : "); Serial.println(humidity);
      Serial.print("SpO2 : "); Serial.println(spo2);
      Serial.print("BPM : "); Serial.println(heartRate);
      Serial.print("Qualité de l'air MQ135 : "); Serial.println(airQuality);

      HTTPClient http;
      http.begin(sensorUrl);
      http.addHeader("Content-Type", "application/json");

      String sensorPayload = "{";
      sensorPayload += "\"temperature\":" + String(temperature) + ",";
      sensorPayload += "\"humidity\":" + String(humidity) + ",";
      sensorPayload += "\"spo2\":" + String(spo2) + ",";
      sensorPayload += "\"bpm\":" + String(heartRate) + ",";
      sensorPayload += "\"air_quality\":" + String(airQuality);
      sensorPayload += "}";

      int httpResponseCode = http.POST(sensorPayload);
      if (httpResponseCode > 0) {
        Serial.println("Données capteurs envoyées !");
      } else {
        Serial.print("Erreur capteurs : ");
        Serial.println(httpResponseCode);
      }
      http.end();
    } else {
      Serial.println("Lecture BPM/SpO2 invalide.");
    }
  }
}
