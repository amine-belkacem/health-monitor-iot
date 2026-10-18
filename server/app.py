from flask import Flask, request, jsonify, send_file, render_template
import sqlite3
from datetime import datetime
import os
import csv

app = Flask(__name__)
DB_FILE = 'ecg_data.db'
CSV_ECG_FILE = 'export_ecg.csv'
CSV_SENSOR_FILE = 'export_sensor.csv'


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Table ECG
    c.execute('''
        CREATE TABLE IF NOT EXISTS ecg (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ecg_value REAL NOT NULL
        )
    ''')

    # Table capteurs généraux
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            spo2 INTEGER,
            bpm INTEGER,
            air_quality INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    print("Base de données initialisée.")


@app.route('/')
def index():
    return render_template('index.html')


# POST données ECG
@app.route('/ecg', methods=['POST'])
def recevoir_ecg():
    data = request.get_json()
    if data and 'ecg_value' in data:
        ecg_valeur = data['ecg_value']
        timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO ecg (timestamp, ecg_value) VALUES (?, ?)",
                  (timestamp, ecg_valeur))
        conn.commit()
        conn.close()

        print(f"✅ Donnée ECG reçue : {ecg_valeur}")
        return jsonify({"status": "reçu et enregistré"}), 200
    return jsonify({"error": "donnée invalide"}), 400


# POST données capteurs généraux
@app.route('/sensor_data', methods=['POST'])
def recevoir_sensor_data():
    data = request.get_json()
    if data is None:
        return jsonify({"error": "pas de données reçues"}), 400

    required_keys = ['temperature', 'humidity', 'spo2', 'bpm', 'air_quality']
    if not all(k in data for k in required_keys):
        return jsonify({"error": "champs manquants dans les données"}), 400

    timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensor_data (timestamp, temperature, humidity, spo2, bpm, air_quality)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, data['temperature'], data['humidity'], data['spo2'],
          data['bpm'], data['air_quality']))
    conn.commit()
    conn.close()

    print(f"Données capteurs reçues : {data}")
    return jsonify({"status": "données capteurs enregistrées"}), 200


# GET dernières 100 données ECG
@app.route('/data', methods=['GET'])
def get_ecg_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, ecg_value FROM ecg ORDER BY id DESC LIMIT 170")
    rows = c.fetchall()
    conn.close()
    data = [{"id": row[0], "ecg_value": row[1]} for row in reversed(rows)]
    return jsonify(data)


# GET dernières 100 données capteurs
@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT temperature, humidity, spo2, bpm, air_quality FROM sensor_data ORDER BY id DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()

    data = []
    for row in reversed(rows):
        data.append({
            "temperature": row[0],
            "humidity": row[1],
            "spo2": row[2],
            "bpm": row[3],
            "air_quality": row[4]
        })
    return jsonify(data)


# Export CSV ECG
@app.route('/export_ecg', methods=['GET'])
def export_csv_ecg():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, ecg_value FROM ecg ORDER BY id")
    rows = c.fetchall()
    conn.close()

    with open(CSV_ECG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'timestamp', 'ecg_value'])
        writer.writerows(rows)

    return send_file(CSV_ECG_FILE, as_attachment=True)


# Export CSV capteurs
@app.route('/export_sensor', methods=['GET'])
def export_csv_sensor():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, temperature, humidity, spo2, bpm, air_quality FROM sensor_data ORDER BY id")
    rows = c.fetchall()
    conn.close()

    with open(CSV_SENSOR_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'timestamp', 'temperature', 'humidity', 'spo2',
                         'bpm', 'air_quality'])
        writer.writerows(rows)

    return send_file(CSV_SENSOR_FILE, as_attachment=True)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
