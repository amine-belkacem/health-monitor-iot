import 'dart:async';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SensorScreen extends StatefulWidget {
  const SensorScreen({super.key});

  @override
  State<SensorScreen> createState() => _SensorScreenState();
}

class _SensorScreenState extends State<SensorScreen> {
  List<SensorReading> _rows = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _refresh());
  }

  Future<void> _refresh() async {
    try {
      final rows = await ApiService.fetchSensors();
      if (mounted) setState(() => _rows = rows);
    } catch (_) {}
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // Une courbe par capteur ; l'axe X compte les mesures (une toutes les 3 s)
  Widget _chart(String title, List<double> values, Color color) {
    final spots = [for (var i = 0; i < values.length; i++) FlSpot(i * 3.0, values[i])];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          SizedBox(
            height: 150,
            child: spots.isEmpty
                ? const Center(child: Text('Pas encore de données'))
                : LineChart(
                    LineChartData(
                      lineBarsData: [
                        LineChartBarData(
                          spots: spots,
                          color: color,
                          barWidth: 2,
                          dotData: const FlDotData(show: false),
                        ),
                      ],
                      titlesData: const FlTitlesData(
                        topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      ),
                    ),
                    duration: Duration.zero,
                  ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Capteurs')),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          _chart('Température (°C)', _rows.map((r) => r.temperature).toList(), Colors.orange),
          _chart('Humidité (%)', _rows.map((r) => r.humidity).toList(), Colors.blue),
          _chart('SpO2 (%)', _rows.map((r) => r.spo2.toDouble()).toList(), Colors.teal),
          _chart('Fréquence cardiaque (bpm)', _rows.map((r) => r.bpm.toDouble()).toList(), Colors.red),
          _chart("Qualité de l'air (brut ADC)", _rows.map((r) => r.airQuality.toDouble()).toList(), Colors.grey),
        ],
      ),
    );
  }
}
