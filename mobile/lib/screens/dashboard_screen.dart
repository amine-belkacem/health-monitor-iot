import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'ecg_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  SensorReading? _last;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
    // autres capteurs rafraîchis toutes les 3 s
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _refresh());
  }

  Future<void> _refresh() async {
    try {
      final rows = await ApiService.fetchSensors();
      if (rows.isNotEmpty && mounted) setState(() => _last = rows.last);
    } catch (_) {
      // l'erreur de connexion est déjà affichée par le graphe ECG
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Widget _card(String label, String value) {
    return Card(
      child: ListTile(
        title: Text(label),
        trailing: Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final s = _last;
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          const Text('Électrocardiogramme (ECG)',
              textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.bold)),
          const EcgChart(height: 160),
          const SizedBox(height: 16),
          const Text('Données des capteurs',
              textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.bold)),
          _card('Température', s == null ? '--' : '${s.temperature} °C'),
          _card('Humidité', s == null ? '--' : '${s.humidity} %'),
          _card('SpO2', s == null ? '--' : '${s.spo2} %'),
          _card('Fréquence cardiaque', s == null ? '--' : '${s.bpm} bpm'),
          _card("Qualité de l'air", s == null ? '--' : '${s.airQuality}'),
        ],
      ),
    );
  }
}
