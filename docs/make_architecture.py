#!/usr/bin/env python3
"""Diagramme d'architecture (PNG) pour le README."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 1600, 780
BG = (248, 250, 252)
INK = (15, 23, 42)
MUTED = (71, 85, 105)
TEAL = (13, 148, 136)
BLUE = (37, 99, 235)
AMBER = (180, 83, 9)
NAVY = (30, 64, 175)
PURPLE = (147, 51, 234)

BOLD = "C:/Windows/Fonts/seguisb.ttf"
REG = "C:/Windows/Fonts/segoeui.ttf"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def box(x, y, w, h, title, lines, accent, fill=(255, 255, 255)):
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=fill, outline=accent, width=3)
    d.rectangle([x, y, x + 9, y + h], fill=accent)
    d.text((x + 26, y + 20), title, font=ImageFont.truetype(BOLD, 25), fill=INK)
    f = ImageFont.truetype(REG, 19)
    for i, line in enumerate(lines):
        d.text((x + 26, y + 60 + i * 26), line, font=f, fill=MUTED)


def poly_arrow(points, color, label="", label_at=0.5):
    d.line(points, fill=color, width=3, joint="curve")
    (x1, y1), (x2, y2) = points[-2], points[-1]
    if abs(x2 - x1) >= abs(y2 - y1):
        sign = 1 if x2 > x1 else -1
        d.polygon([(x2, y2), (x2 - 13 * sign, y2 - 6), (x2 - 13 * sign, y2 + 6)], fill=color)
    else:
        sign = 1 if y2 > y1 else -1
        d.polygon([(x2, y2), (x2 - 6, y2 - 13 * sign), (x2 + 6, y2 - 13 * sign)], fill=color)
    if label:
        # position le long du segment le plus long
        segs = list(zip(points, points[1:]))
        segs.sort(key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]), reverse=True)
        (ax, ay), (bx, by) = segs[0]
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        f = ImageFont.truetype(BOLD, 16)
        tw = d.textlength(label, font=f)
        horizontal = abs(bx - ax) >= abs(by - ay)
        if horizontal:
            d.rectangle([cx - tw / 2 - 8, cy - 27, cx + tw / 2 + 8, cy - 3], fill=BG)
            d.text((cx - tw / 2, cy - 27), label, font=f, fill=color)
        else:
            d.rectangle([cx + 8, cy - 12, cx + tw + 16, cy + 10], fill=BG)
            d.text((cx + 12, cy - 12), label, font=f, fill=color)


d.text((60, 42), "Architecture du système", font=ImageFont.truetype(BOLD, 36), fill=INK)
d.text((60, 92), "ESP32 → Wi-Fi → Flask / Raspberry Pi 5 → SQLite → interfaces web et mobile",
       font=ImageFont.truetype(REG, 20), fill=MUTED)

box(60, 180, 380, 210, "ESP32 + capteurs", [
    "AD8232   → ECG (GPIO34)",
    "MAX30102 → SpO₂ / BPM (I2C)",
    "DHT22    → T° / humidité (GPIO27)",
    "MQ-135   → qualité d'air (GPIO35)",
], TEAL)

box(520, 180, 300, 210, "Wi-Fi 802.11", [
    "Réseau local du domicile",
    "POST /ecg  (en continu)",
    "POST /sensor_data  (3 s)",
], BLUE, fill=(239, 246, 255))

box(900, 150, 460, 280, "Flask — Raspberry Pi 5", [
    "POST  /ecg  ·  /sensor_data",
    "GET   /data  ·  /sensor_data",
    "GET   /export_ecg  ·  /export_sensor",
    "GET   /  → page web (Chart.js)",
], AMBER)

# encart SQLite dans la carte Flask
d.rounded_rectangle([930, 356, 1330, 404], radius=10, fill=(255, 251, 235),
                    outline=AMBER, width=2)
d.text((946, 370), "SQLite  ecg_data.db  ·  tables ecg, sensor_data",
       font=ImageFont.truetype(REG, 17), fill=MUTED)

box(500, 560, 340, 150, "Page web (Chart.js)", [
    "Dashboard · ECG · Capteurs",
    "Export CSV · reset du graphe ECG",
], NAVY, fill=(248, 250, 252))

box(900, 570, 420, 150, "Application Flutter", [
    "Android · fl_chart · alertes",
], PURPLE, fill=(250, 245, 255))

poly_arrow([(442, 285), (516, 285)], INK)
poly_arrow([(822, 285), (896, 285)], BLUE, "Wi-Fi")
poly_arrow([(900, 400), (860, 400), (860, 556)], NAVY, "HTTP GET / JSON")
poly_arrow([(1120, 432), (1120, 566)], PURPLE, "HTTP GET / JSON")

d.text((60, 748), "Les clients n'accèdent jamais directement à SQLite : tout passe par l'API Flask. "
                  "Ngrok peut exposer ce serveur en WAN.",
       font=ImageFont.truetype(REG, 17), fill=MUTED)

img.save(os.path.join(HERE, "architecture.png"))
print("écrit", os.path.join(HERE, "architecture.png"))
