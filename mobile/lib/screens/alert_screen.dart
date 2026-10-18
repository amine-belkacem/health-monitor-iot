import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

// Seuils par défaut (fenêtre « Modifier les seuils » du rapport, figure 3.21)
const Map<String, double> defaultThresholds = {
  'temperature': 39.0,
  'humidity': 80.0,
  'spo2': 90.0,
  'bpm': 130.0,
  'air_quality': 300.0,
};

class AlertItem {
  final String label;
  final String value;
  final DateTime time;
  AlertItem(this.label, this.value, this.time);
}

// Compare une mesure aux seuils. Pour la SpO2 l'alerte se déclenche sous le seuil,
// pour les autres capteurs au-dessus.
List<AlertItem> checkThresholds(SensorReading r, Map<String, double> t, DateTime now) {
  final alerts = <AlertItem>[];
  if (r.temperature > t['temperature']!) alerts.add(AlertItem('Température élevée', '${r.temperature} °C', now));
  if (r.humidity > t['humidity']!) alerts.add(AlertItem('Humidité élevée', '${r.humidity} %', now));
  if (r.spo2 < t['spo2']!) alerts.add(AlertItem('Saturation trop basse', '${r.spo2} %', now));
  if (r.bpm > t['bpm']!) alerts.add(AlertItem('Rythme cardiaque élevé', '${r.bpm} bpm', now));
  if (r.airQuality > t['air_quality']!) alerts.add(AlertItem("Qualité de l'air dégradée", '${r.airQuality}', now));
  return alerts;
}

class AlertScreen extends StatefulWidget {
  const AlertScreen({super.key});

  @override
  State<AlertScreen> createState() => _AlertScreenState();
}

class _AlertScreenState extends State<AlertScreen> {
  Map<String, double> _thresholds = Map.of(defaultThresholds);
  final List<AlertItem> _alerts = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _loadThresholds();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _check());
  }

  Future<void> _loadThresholds() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      for (final k in defaultThresholds.keys) {
        _thresholds[k] = prefs.getDouble('seuil_$k') ?? defaultThresholds[k]!;
      }
    });
  }

  Future<void> _saveThresholds() async {
    final prefs = await SharedPreferences.getInstance();
    for (final e in _thresholds.entries) {
      await prefs.setDouble('seuil_${e.key}', e.value);
    }
  }

  Future<void> _check() async {
    try {
      final rows = await ApiService.fetchSensors();
      if (rows.isEmpty || !mounted) return;
      final found = checkThresholds(rows.last, _thresholds, DateTime.now());
      if (found.isNotEmpty) {
        setState(() {
          _alerts.insertAll(0, found);
          if (_alerts.length > 50) _alerts.removeRange(50, _alerts.length);
        });
      }
    } catch (_) {}
  }

  void _editThresholds() {
    final controllers = {
      for (final e in _thresholds.entries) e.key: TextEditingController(text: e.value.toString())
    };
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Modifier les seuils'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final k in controllers.keys)
                TextField(
                  controller: controllers[k],
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(labelText: 'Seuil ${k.toUpperCase()}'),
                ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          TextButton(
            onPressed: () {
              setState(() {
                for (final k in controllers.keys) {
                  _thresholds[k] = double.tryParse(controllers[k]!.text) ?? _thresholds[k]!;
                }
              });
              _saveThresholds();
              Navigator.pop(ctx);
            },
            child: const Text('Valider'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alerte – Seuils Critiques'),
        actions: [IconButton(icon: const Icon(Icons.edit), onPressed: _editThresholds)],
      ),
      body: _alerts.isEmpty
          ? const Center(child: Text('Aucune anomalie détectée'))
          : ListView.builder(
              itemCount: _alerts.length,
              itemBuilder: (_, i) {
                final a = _alerts[i];
                final t = a.time;
                final hh = '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}:${t.second.toString().padLeft(2, '0')}';
                return Card(
                  color: Colors.red.shade50,
                  child: ListTile(
                    leading: const Icon(Icons.warning, color: Colors.red),
                    title: Text(a.label),
                    subtitle: Text('Valeur : ${a.value}'),
                    trailing: Text(hh),
                  ),
                );
              },
            ),
    );
  }
}
