import 'package:flutter/material.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('À propos')),
      body: const Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.monitor_heart, size: 80, color: Colors.teal),
            SizedBox(height: 16),
            Text('Faculté de Génie Électrique',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('Master 2 – Électronique des Systèmes Embarqués',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 16)),
            SizedBox(height: 24),
            Text('Système de santé connecté : ESP32, Raspberry Pi 5, Flask, SQLite',
                textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
