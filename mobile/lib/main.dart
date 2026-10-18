import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/ecg_screen.dart';
import 'screens/sensor_screen.dart';
import 'screens/about_screen.dart';
import 'screens/alert_screen.dart';

void main() {
  runApp(HealthMonitorApp());
}

class HealthMonitorApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Système de Santé Connecté',
      theme: ThemeData(primarySwatch: Colors.teal),
      home: MainNavigation(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  @override
  _MainNavigationState createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    DashboardScreen(),
    ECGScreen(),
    SensorScreen(),
    AlertScreen(),
    AboutScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        selectedItemColor: Colors.teal,
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.favorite), label: 'ECG'),
          BottomNavigationBarItem(icon: Icon(Icons.sensors), label: 'Capteurs'),
          BottomNavigationBarItem(icon: Icon(Icons.warning), label: 'Alertes'),
          BottomNavigationBarItem(icon: Icon(Icons.info), label: 'À propos'),
        ],
        onTap: (index) => setState(() => _currentIndex = index),
      ),
    );
  }
}
