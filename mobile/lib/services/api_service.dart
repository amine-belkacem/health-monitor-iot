import 'dart:convert';
import 'package:http/http.dart' as http;

// Adresse du serveur Flask : IP locale du Raspberry Pi, ou l'URL publique Ngrok
const String baseUrl = 'http://192.168.1.4:5000';

class EcgPoint {
  final int id;
  final double value;
  EcgPoint(this.id, this.value);
}

class SensorReading {
  final double temperature;
  final double humidity;
  final int spo2;
  final int bpm;
  final int airQuality;

  SensorReading({
    required this.temperature,
    required this.humidity,
    required this.spo2,
    required this.bpm,
    required this.airQuality,
  });

  factory SensorReading.fromJson(Map<String, dynamic> j) => SensorReading(
        temperature: (j['temperature'] as num).toDouble(),
        humidity: (j['humidity'] as num).toDouble(),
        spo2: (j['spo2'] as num).toInt(),
        bpm: (j['bpm'] as num).toInt(),
        airQuality: (j['air_quality'] as num).toInt(),
      );
}

class ApiService {
  static const _timeout = Duration(seconds: 3);

  // GET /data : dernières valeurs ECG
  static Future<List<EcgPoint>> fetchEcg() async {
    final res = await http.get(Uri.parse('$baseUrl/data')).timeout(_timeout);
    if (res.statusCode != 200) throw Exception('HTTP ${res.statusCode}');
    final List rows = jsonDecode(res.body);
    return rows
        .map((r) => EcgPoint((r['id'] as num).toInt(), (r['ecg_value'] as num).toDouble()))
        .toList();
  }

  // GET /sensor_data : dernières mesures des autres capteurs
  static Future<List<SensorReading>> fetchSensors() async {
    final res = await http.get(Uri.parse('$baseUrl/sensor_data')).timeout(_timeout);
    if (res.statusCode != 200) throw Exception('HTTP ${res.statusCode}');
    final List rows = jsonDecode(res.body);
    return rows.map((r) => SensorReading.fromJson(r)).toList();
  }
}
