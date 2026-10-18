import 'package:flutter_test/flutter_test.dart';
import 'package:health_monitor/screens/alert_screen.dart';
import 'package:health_monitor/services/api_service.dart';

// Tests de la logique d'alerte avec les seuils par défaut de l'application
// (fenêtre « Modifier les seuils », figure 3.21 du mémoire) :
//   température > 39.0, humidité > 80.0, SpO2 < 90.0, BPM > 130.0, air > 300.0

SensorReading reading({
  double temperature = 37.4,
  double humidity = 47.5,
  int spo2 = 98,
  int bpm = 82,
  int airQuality = 226,
}) =>
    SensorReading(
      temperature: temperature,
      humidity: humidity,
      spo2: spo2,
      bpm: bpm,
      airQuality: airQuality,
    );

List<String> labels(SensorReading r) =>
    checkThresholds(r, defaultThresholds, DateTime(2025, 6, 8)).map((a) => a.label).toList();

void main() {
  test('mesure réelle de la figure 3.24 : aucune alerte', () {
    // 37.4 °C, 47.5 %, SpO2 98 %, 82 BPM, air 226
    expect(labels(reading()), isEmpty);
  });

  test('les seuils sont stricts : une valeur égale au seuil ne déclenche rien', () {
    expect(labels(reading(temperature: 39.0, humidity: 80.0, spo2: 90, bpm: 130, airQuality: 300)),
        isEmpty);
  });

  test('chaque capteur déclenche sa propre alerte', () {
    expect(labels(reading(temperature: 39.1)), ['Température élevée']);
    expect(labels(reading(humidity: 80.1)), ['Humidité élevée']);
    expect(labels(reading(spo2: 89)), ['Saturation trop basse']);
    expect(labels(reading(bpm: 131)), ['Rythme cardiaque élevé']);
    expect(labels(reading(airQuality: 301)), ["Qualité de l'air dégradée"]);
  });

  test('cinq dépassements en même temps donnent cinq alertes', () {
    final r = reading(temperature: 40, humidity: 90, spo2: 85, bpm: 150, airQuality: 400);
    expect(labels(r).length, 5);
  });

  test('la valeur mesurée est recopiée dans l\'alerte', () {
    final alerts = checkThresholds(reading(bpm: 142), defaultThresholds, DateTime(2025, 6, 8));
    expect(alerts.single.value, '142 bpm');
  });

  test('JSON du serveur -> SensorReading (types int/double mélangés)', () {
    final r = SensorReading.fromJson({
      'temperature': 37,
      'humidity': 47.5,
      'spo2': 98,
      'bpm': 82,
      'air_quality': 226,
    });
    expect(r.temperature, 37.0);
    expect(r.airQuality, 226);
  });
}
