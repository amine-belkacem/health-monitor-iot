"""
Tests du serveur Flask (server/app.py).

Les stimuli sont les vraies mesures du mémoire : les 22 lignes de la figure 3.16
(export CSV du 8 juin 2025) et des valeurs ECG brutes vues pendant les essais.
Chaque test compare la valeur obtenue à la valeur attendue et affiche
"ECHEC ... obtenu ..., attendu ..." en cas d'écart.

Lancement : pytest tests/
"""
import csv
import importlib.util
import io
import os

import pytest

SERVER = os.path.join(os.path.dirname(__file__), "..", "server", "app.py")

# Figure 3.16 : (temperature, humidity, spo2, bpm, air_quality)
THESIS_READINGS = [
    (36.2, 53.9, 98, 82, 220), (36.5, 51.0, 98, 83, 108), (36.2, 54.3, 98, 72, 137),
    (37.8, 45.2, 96, 75, 203), (37.7, 53.6, 98, 76, 125), (36.0, 57.8, 97, 71, 278),
    (37.6, 56.0, 98, 77, 187), (36.5, 53.2, 97, 81, 213), (37.3, 53.6, 97, 70, 153),
    (37.5, 46.7, 98, 82, 146), (36.9, 44.3, 98, 83, 122), (37.2, 52.0, 98, 71, 226),
    (36.7, 50.2, 96, 84, 214), (36.1, 52.7, 98, 70, 173), (36.2, 45.1, 98, 71, 277),
    (36.1, 43.4, 97, 82, 175), (36.7, 50.9, 98, 84, 109), (37.7, 55.0, 98, 75, 156),
    (37.0, 41.1, 96, 83, 188), (37.1, 47.3, 96, 72, 201), (37.2, 52.9, 98, 78, 168),
    (36.5, 48.2, 98, 82, 258),
]
KEYS = ["temperature", "humidity", "spo2", "bpm", "air_quality"]


def check(obtenu, attendu, quoi):
    assert obtenu == attendu, f"ECHEC {quoi} : obtenu {obtenu!r}, attendu {attendu!r}"


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Le serveur écrit ecg_data.db et les CSV dans le dossier courant :
    # on se place dans un dossier temporaire pour partir d'une base vide.
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location("app", SERVER)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app_module.init_db()
    app_module.app.testing = True
    return app_module.app.test_client()


def post_readings(client, readings):
    for i, r in enumerate(readings):
        res = client.post("/sensor_data", json=dict(zip(KEYS, r)))
        check(res.status_code, 200, f"POST /sensor_data ligne {i + 1}")


# ---------- /sensor_data ----------

def test_sensor_readings_from_thesis_are_stored_in_order(client):
    post_readings(client, THESIS_READINGS)
    rows = client.get("/sensor_data").get_json()
    check(len(rows), 22, "nombre de lignes renvoyées")
    for i, (row, expected) in enumerate(zip(rows, THESIS_READINGS)):
        check(tuple(row[k] for k in KEYS), expected, f"ligne {i + 1}")


def test_sensor_data_missing_field_is_rejected(client):
    res = client.post("/sensor_data", json={"temperature": 37.4, "humidity": 47.5})
    check(res.status_code, 400, "POST /sensor_data avec champs manquants")
    check(client.get("/sensor_data").get_json(), [], "base après une requête refusée")


def test_sensor_data_without_json_is_rejected(client):
    # Flask refuse lui-même un corps qui n'est pas du JSON (415 Unsupported Media Type)
    res = client.post("/sensor_data", data="pas du json", content_type="text/plain")
    check(res.status_code, 415, "POST /sensor_data avec un corps texte")


def test_sensor_data_returns_last_100_only(client):
    # 22 lignes x 5 = 110 mesures : la route ne renvoie que les 100 dernières
    post_readings(client, THESIS_READINGS * 5)
    rows = client.get("/sensor_data").get_json()
    check(len(rows), 100, "taille de la fenêtre /sensor_data")
    # la 11e mesure envoyée est la plus ancienne gardée : THESIS_READINGS[10]
    check(tuple(rows[0][k] for k in KEYS), THESIS_READINGS[10], "plus ancienne ligne gardée")
    check(tuple(rows[-1][k] for k in KEYS), THESIS_READINGS[21], "ligne la plus récente")


# ---------- /ecg et /data ----------

def test_ecg_values_come_back_with_their_id(client):
    # valeurs brutes de la figure 3.17 (table ecg pendant les essais)
    values = [0, 0, 4095, 0, 0, 0, 638]
    for v in values:
        check(client.post("/ecg", json={"ecg_value": v}).status_code, 200, f"POST /ecg {v}")
    rows = client.get("/data").get_json()
    check([r["ecg_value"] for r in rows], [float(v) for v in values], "valeurs ECG")
    check([r["id"] for r in rows], list(range(1, 8)), "id des lignes ECG")


def test_ecg_without_value_is_rejected(client):
    check(client.post("/ecg", json={"value": 1.2}).status_code, 400, "POST /ecg sans ecg_value")
    check(client.get("/data").get_json(), [], "table ecg après une requête refusée")


def test_ecg_window_is_170_samples(client):
    for v in range(200):
        client.post("/ecg", json={"ecg_value": v})
    rows = client.get("/data").get_json()
    check(len(rows), 170, "taille de la fenêtre /data")
    check(rows[0]["id"], 31, "id le plus ancien (200 - 170 + 1)")
    check(rows[-1]["id"], 200, "id le plus récent")


# ---------- export CSV ----------

def test_sensor_csv_export(client):
    post_readings(client, THESIS_READINGS)
    res = client.get("/export_sensor")
    check(res.status_code, 200, "GET /export_sensor")
    lines = list(csv.reader(io.StringIO(res.data.decode())))
    check(lines[0], ["id", "timestamp"] + KEYS, "en-tête CSV")
    check(len(lines), 23, "1 en-tête + 22 lignes")
    check(lines[1][2:], ["36.2", "53.9", "98", "82", "220"], "première ligne CSV")


def test_ecg_csv_export(client):
    client.post("/ecg", json={"ecg_value": 638})
    lines = list(csv.reader(io.StringIO(client.get("/export_ecg").data.decode())))
    check(lines[0], ["id", "timestamp", "ecg_value"], "en-tête CSV ECG")
    check(lines[1][2], "638.0", "valeur ECG exportée")
