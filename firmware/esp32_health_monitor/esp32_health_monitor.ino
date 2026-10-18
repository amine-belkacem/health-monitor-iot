#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include "ecg_conversion.h"

// Wi-Fi (à remplir avant de flasher, ne jamais publier les vrais identifiants)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Serveur Flask (IP du Raspberry Pi 5)
const char* ecgUrl = "http://192.168.1.4:5000/ecg";
const char* sensorUrl = "http://192.168.1.4:5000/sensor_data";

// ECG AD8232
const int ecgPin = 34;
const int loPlusPin = 32;   // LO+ : électrode positive décollée
const int loMinusPin = 33;  // LO- : électrode négative décollée

// DHT22
#define DHTPIN 27
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// MQ135
const int mq135Pin = 35;

// MAX30102
MAX30105 particleSensor;
#define MAX_SAMPLES 100          // 100 échantillons à 25 Hz = 4 s de signal
uint32_t irBuffer[MAX_SAMPLES];
uint32_t redBuffer[MAX_SAMPLES];
int sampleIndex = 0;
int32_t spo2;
int8_t validSpO2;
int32_t heartRate;
int8_t validHeartRate;
int32_t lastSpo2 = -1;           // dernières valeurs valides
int32_t lastHeartRate = -1;

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

  pinMode(loPlusPin, INPUT);
  pinMode(loMinusPin, INPUT);
  dht.begin();

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 non détecté !");
    while (1);
  }

  // Configuration attendue par l'algorithme Maxim : 100 Hz / moyenne de 4 = 25 Hz
  // (luminosité LED, moyenne, mode rouge+IR, fréquence, largeur d'impulsion, plage ADC)
  particleSensor.setup(60, 4, 2, 100, 411, 4096);
}

// Envoie un JSON en HTTP POST, renvoie le code HTTP (négatif si erreur réseau)
int postJson(const char* url, const String& payload) {
  if (WiFi.status() != WL_CONNECTED) return -1;
  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(payload);
  http.end();
  return code;
}

// Lecture non bloquante du MAX30102 : on vide la FIFO du capteur à chaque tour
// de loop(), et on lance le calcul SpO2/BPM quand le buffer de 100 est plein.
void readMax30102() {
  particleSensor.check();
  while (particleSensor.available() && sampleIndex < MAX_SAMPLES) {
    redBuffer[sampleIndex] = particleSensor.getFIFORed();
    irBuffer[sampleIndex] = particleSensor.getFIFOIR();
    particleSensor.nextSample();
    sampleIndex++;
  }

  if (sampleIndex == MAX_SAMPLES) {
    maxim_heart_rate_and_oxygen_saturation(irBuffer, MAX_SAMPLES, redBuffer,
                                           &spo2, &validSpO2, &heartRate, &validHeartRate);
    if (validSpO2) lastSpo2 = spo2;
    if (validHeartRate) lastHeartRate = heartRate;
    sampleIndex = 0;
  }
}

void loop() {
  // ECG : si une électrode est décollée, la sortie AD8232 part en butée,
  // on n'envoie donc rien plutôt qu'une valeur fausse
  bool leadsOff = digitalRead(loPlusPin) == HIGH || digitalRead(loMinusPin) == HIGH;
  if (leadsOff) {
    Serial.println("ECG : électrode décollée");
  } else {
    int raw = analogRead(ecgPin);
    float ecgMv = ecgAdcToMillivolts(raw);
    Serial.print("ECG (mV): "); Serial.println(ecgMv, 3);

    String ecgPayload = "{\"ecg_value\":" + String(ecgMv, 3) + "}";
    int code = postJson(ecgUrl, ecgPayload);
    if (code <= 0) {
      Serial.print("Erreur ECG : "); Serial.println(code);
    }
  }

  readMax30102();

  // Autres capteurs toutes les 3 secondes
  if (millis() - lastSensorSent > sensorInterval) {
    lastSensorSent = millis();

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    int airQuality = analogRead(mq135Pin);   // valeur ADC brute (0-4095), pas des ppm

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Lecture DHT22 invalide.");
      return;
    }
    if (lastSpo2 < 0 || lastHeartRate < 0) {
      Serial.println("Lecture BPM/SpO2 invalide (doigt mal placé ?).");
      return;
    }

    Serial.print("Température : "); Serial.print(temperature); Serial.println(" °C");
    Serial.print("Humidité : "); Serial.print(humidity); Serial.println(" %");
    Serial.print("SpO2 : "); Serial.print(lastSpo2); Serial.println(" %");
    Serial.print("BPM : "); Serial.println(lastHeartRate);
    Serial.print("Qualité air (MQ135) : "); Serial.println(airQuality);

    String sensorPayload = "{";
    sensorPayload += "\"temperature\":" + String(temperature, 1) + ",";
    sensorPayload += "\"humidity\":" + String(humidity, 1) + ",";
    sensorPayload += "\"spo2\":" + String(lastSpo2) + ",";
    sensorPayload += "\"bpm\":" + String(lastHeartRate) + ",";
    sensorPayload += "\"air_quality\":" + String(airQuality);
    sensorPayload += "}";

    int code = postJson(sensorUrl, sensorPayload);
    if (code > 0) {
      Serial.print("Données capteurs envoyées ! Code: "); Serial.println(code);
    } else {
      Serial.print("Erreur capteurs : "); Serial.println(code);
    }
  }

  delay(10);
}
