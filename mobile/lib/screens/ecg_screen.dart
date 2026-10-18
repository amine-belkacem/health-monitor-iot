import 'dart:async';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

// Graphe ECG réutilisé par le Dashboard et par l'écran ECG
class EcgChart extends StatefulWidget {
  final double height;
  const EcgChart({super.key, this.height = 200});

  @override
  State<EcgChart> createState() => _EcgChartState();
}

class _EcgChartState extends State<EcgChart> {
  List<EcgPoint> _points = [];
  Timer? _timer;
  String? _error;

  @override
  void initState() {
    super.initState();
    _refresh();
    // ECG rafraîchi toutes les 500 ms
    _timer = Timer.periodic(const Duration(milliseconds: 500), (_) => _refresh());
  }

  Future<void> _refresh() async {
    try {
      final pts = await ApiService.fetchEcg();
      if (mounted) setState(() { _points = pts; _error = null; });
    } catch (e) {
      if (mounted) setState(() => _error = 'Serveur injoignable');
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return SizedBox(height: widget.height, child: Center(child: Text(_error!)));
    }
    if (_points.isEmpty) {
      return SizedBox(height: widget.height, child: const Center(child: Text('En attente de données ECG...')));
    }
    final spots = [
      for (var i = 0; i < _points.length; i++) FlSpot(i.toDouble(), _points[i].value)
    ];
    return SizedBox(
      height: widget.height,
      child: LineChart(
        LineChartData(
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: false,
              color: Colors.redAccent,
              barWidth: 1.5,
              dotData: const FlDotData(show: false),
            ),
          ],
          titlesData: const FlTitlesData(show: false),
          gridData: const FlGridData(show: true),
          borderData: FlBorderData(show: false),
        ),
        duration: Duration.zero,
      ),
    );
  }
}

class ECGScreen extends StatelessWidget {
  const ECGScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Électrocardiogramme (ECG)')),
      body: const Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          children: [
            EcgChart(height: 320),
            SizedBox(height: 12),
            Text('Valeurs en mV, fenêtre des 170 derniers échantillons reçus.'),
          ],
        ),
      ),
    );
  }
}
