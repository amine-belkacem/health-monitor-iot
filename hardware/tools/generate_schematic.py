#!/usr/bin/env python3
"""Schéma électrique : SVG (livrable) + PNG (aperçu) + export JSON structuré."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)

W, H = 1500, 980
SX1, SX2 = 1016, 1420
EX2 = 470
INK = "#1b2733"
MUTED = "#5b6b7b"
RED = "#c0392b"
ORANGE = "#b9770e"
BLUE = "#1f5f8b"
PURPLE = "#7d3c98"
TEAL = "#0e6655"
GREEN = "#1e8449"

prims = []


def text(x, y, s, size=14, anchor="start", color=INK, weight="normal"):
    prims.append({"t": "text", "x": x, "y": y, "s": s, "size": size,
                  "anchor": anchor, "color": color, "weight": weight})


def line(x1, y1, x2, y2, color=INK, w=1.4, dash=None):
    prims.append({"t": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                  "color": color, "w": w, "dash": dash})


def rect(x, y, w, h, fill="#f7fafc", stroke=INK, rx=8, sw=1.6, dash=None):
    prims.append({"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill,
                  "stroke": stroke, "rx": rx, "sw": sw, "dash": dash})


def path(pts, color, w=2.2):
    prims.append({"t": "path", "pts": pts, "color": color, "w": w})


# ------------------------------------------------------------------ cadre
rect(20, 20, W - 40, H - 40, fill="none", stroke="#94a3b8", rx=4, sw=1.2)
text(46, 58, "Système de santé connecté — schéma électrique", 23, weight="bold")
text(46, 84, "ESP32 · AD8232 (ECG) · MAX30102 (SpO₂ / BPM) · DHT22 · MQ-135", 14, color=MUTED)

# ------------------------------------------------------------------ ESP32
EX1, EY1, EY2 = 90, 110, 860
rect(EX1, EY1, EX2 - EX1, EY2 - EY1, fill="#f8fbfd")
text(EX1 + 18, EY1 + 32, "U1 — ESP32 DevKit V1", 17, weight="bold")
text(EX1 + 18, EY1 + 52, "30 broches · Wi-Fi 802.11 · ADC 12 bits", 12, color=MUTED)

PINS = [("3V3", 170), ("GND", 206), ("GPIO34", 262), ("GPIO32", 312), ("GPIO33", 362),
        ("GPIO27", 412), ("GPIO21", 462), ("GPIO22", 512), ("GPIO35", 562), ("VIN (5 V)", 632)]
for name, y in PINS:
    line(EX2, y, EX2 + 34, y)
    text(EX2 - 14, y + 5, name, 14, anchor="end")

# ------------------------------------------------------------------ capteurs
def sensor_block(title, subtitle, y1, y2, pins):
    rect(SX1, y1, SX2 - SX1, y2 - y1, fill="#fbfdfe")
    text(SX1 + 16, y1 + 28, title, 16, weight="bold")
    text(SX1 + 16, y1 + 46, subtitle, 11.5, color=MUTED)
    for pname, y in pins:
        line(SX1 - 34, y, SX1, y)
        text(SX1 + 12, y + 5, pname, 13.5)


sensor_block("J1 — AD8232", "Front-end ECG, gain ≈ 1100", 110, 364,
             [("GND", 190), ("3.3V", 222), ("OUTPUT", 258), ("LO-", 288),
              ("LO+", 318), ("SDN", 352)])
sensor_block("J2 — DHT22", "Température / humidité (One-Wire)", 380, 520,
             [("VCC", 452), ("DATA", 480), ("GND", 508)])
sensor_block("J4 — MAX30102", "SpO₂ + fréquence cardiaque (I2C)", 540, 740,
             [("VIN", 616), ("GND", 646), ("SDA", 676), ("SCL", 706), ("INT", 734)])
sensor_block("J3 — MQ-135", "Qualité de l'air (analogique)", 760, 960,
             [("VCC", 840), ("GND", 868), ("AOUT", 896), ("DOUT", 924)])

# ------------------------------------------------------------------ pistes
ROUTES = {
    "ECG_OUT": [(EX2 + 34, 258), (SX1 - 34, 258)],
    "LO_MINUS": [(EX2 + 34, 312), (640, 312), (640, 288), (SX1 - 34, 288)],
    "LO_PLUS": [(EX2 + 34, 362), (680, 362), (680, 318), (SX1 - 34, 318)],
    "DHT_DATA": [(EX2 + 34, 412), (600, 412), (600, 480), (SX1 - 34, 480)],
    "SDA": [(EX2 + 34, 462), (560, 462), (560, 676), (SX1 - 34, 676)],
    "SCL": [(EX2 + 34, 512), (530, 512), (530, 706), (SX1 - 34, 706)],
    "MQ_AOUT": [(EX2 + 34, 562), (520, 562), (520, 896), (SX1 - 34, 896)],
}
NET_COLOR = {"ECG_OUT": GREEN, "LO_PLUS": PURPLE, "LO_MINUS": PURPLE,
             "DHT_DATA": BLUE, "SDA": TEAL, "SCL": TEAL, "MQ_AOUT": ORANGE}

LABEL_POS = {"ECG_OUT": (860, 250), "LO_MINUS": (860, 280), "LO_PLUS": (860, 310),
             "DHT_DATA": (860, 472), "SDA": (860, 668), "SCL": (860, 698),
             "MQ_AOUT": (860, 888)}

for net, pts in ROUTES.items():
    path(pts, NET_COLOR[net], 2.2)
    lx, ly = LABEL_POS[net]
    text(lx, ly, net, 10.5, color=NET_COLOR[net], weight="bold")

# ------------------------------------------------------------------ alims
POWER = {"3V3": RED, "GND": "#111827", "5V": ORANGE, "NC": "#64748b"}


def power_flag(kind, x, y, net, show_text=True):
    col = POWER[net]
    if kind == "gnd":
        line(x - 12, y + 6, x + 12, y + 6, col, 2.4)
        line(x - 8, y + 11, x + 8, y + 11, col, 2.4)
        line(x - 4, y + 16, x + 4, y + 16, col, 2.4)
    elif kind == "nc":
        line(x - 6, y - 6, x + 6, y + 6, col, 1.8)
        line(x - 6, y + 6, x + 6, y - 6, col, 1.8)
    else:
        line(x, y + 12, x, y - 6, col, 2.4)
        line(x - 8, y - 6, x + 8, y - 6, col, 2.4)
    if show_text:
        text(x - 14, y + 4, net, 10.5, anchor="end", color=col, weight="bold")


for net, y in (("3V3", 170), ("GND", 206), ("5V", 632)):
    power_flag("gnd" if net == "GND" else "label", EX2 + 44, y, net, show_text=False)

for kind, net, y in [("gnd", "GND", 190), ("label", "3V3", 222), ("label", "3V3", 352),
                     ("label", "3V3", 452), ("gnd", "GND", 508),
                     ("label", "3V3", 616), ("gnd", "GND", 646), ("nc", "NC", 734),
                     ("label", "5V", 840), ("gnd", "GND", 868), ("nc", "NC", 924)]:
    power_flag(kind, SX1 - 44, y, net)

# ------------------------------------------------------------------ notes
rect(100, 640, 340, 170, fill="#fffdf5", stroke="#d6c08a", dash=(5, 4))
text(114, 668, "Notes", 13, weight="bold", color="#8a6d1f")
notes = [
    "SDN (AD8232) tiré à 3V3 : module actif.",
    "MQ-135 alimenté en 5 V (VIN) ; AOUT",
    "lu sur l'ADC 12 bits (GPIO35).",
    "GND commun ; 3V3 fourni par l'ESP32.",
    "Alimentation carte : USB 5 V.",
    "Aucun filtrage analogique additionnel.",
]
for i, n in enumerate(notes):
    text(114, 692 + i * 19, "• " + n, 11.5, color="#6b5a2a")

# ------------------------------------------------------------------ cartouche
rect(46, 878, 424, 72, fill="#ffffff", rx=4)
line(46, 908, 470, 908, INK, 1)
text(60, 899, "Système de santé connecté — monitoring des paramètres vitaux", 11.5, weight="bold")
text(60, 931, "USTHB — FGE — M2 Électronique / SE", 11, color=MUTED)
text(60, 944, "Rév. A — Feuille 1/1 — Dessiné par M. A. Belkacem", 10.5, color=MUTED)

# ------------------------------------------------------------------ rendu SVG
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
       '<rect width="100%" height="100%" fill="#ffffff"/>']
for p in prims:
    if p["t"] == "rect":
        d = f' stroke-dasharray="{" ".join(map(str, p["dash"]))}"' if p["dash"] else ""
        fill = "none" if p["fill"] == "none" else p["fill"]
        svg.append(f'<rect x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" '
                   f'rx="{p["rx"]}" fill="{fill}" stroke="{p["stroke"]}" '
                   f'stroke-width="{p["sw"]}"{d}/>')
    elif p["t"] == "line":
        d = f' stroke-dasharray="{" ".join(map(str, p["dash"]))}"' if p["dash"] else ""
        svg.append(f'<line x1="{p["x1"]}" y1="{p["y1"]}" x2="{p["x2"]}" y2="{p["y2"]}" '
                   f'stroke="{p["color"]}" stroke-width="{p["w"]}" stroke-linecap="round"{d}/>')
    elif p["t"] == "path":
        d = "M " + " L ".join(f"{x} {y}" for x, y in p["pts"])
        svg.append(f'<path d="{d}" fill="none" stroke="{p["color"]}" stroke-width="{p["w"]}" '
                   f'stroke-linejoin="round" stroke-linecap="round"/>')
    elif p["t"] == "text":
        svg.append(f'<text x="{p["x"]}" y="{p["y"]}" font-family="Segoe UI, Arial, sans-serif" '
                   f'font-size="{p["size"]}" fill="{p["color"]}" text-anchor="{p["anchor"]}" '
                   f'font-weight="{"bold" if p["weight"] == "bold" else "normal"}">{esc(p["s"])}</text>')
svg.append("</svg>")
open(os.path.join(HW, "schematic.svg"), "w", encoding="utf-8").write("\n".join(svg))

# ------------------------------------------------------------------ rendu PNG
PNG_W = 1800
S = PNG_W / W
PNG_H = int(H * S)
img = Image.new("RGB", (PNG_W, PNG_H), "white")
dr = ImageDraw.Draw(img)
_cache = {}


def font(size, bold):
    key = (round(size, 1), bold)
    if key not in _cache:
        path = "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
        _cache[key] = ImageFont.truetype(path, max(8, int(size * S * 1.15)))
    return _cache[key]


for p in prims:
    if p["t"] == "rect":
        dr.rounded_rectangle([p["x"] * S, p["y"] * S, (p["x"] + p["w"]) * S, (p["y"] + p["h"]) * S],
                             radius=p["rx"] * S,
                             fill=None if p["fill"] == "none" else p["fill"],
                             outline=p["stroke"], width=max(1, int(p["sw"] * S)))
    elif p["t"] == "line":
        dr.line([p["x1"] * S, p["y1"] * S, p["x2"] * S, p["y2"] * S],
                fill=p["color"], width=max(1, int(p["w"] * S)))
    elif p["t"] == "path":
        dr.line([(x * S, y * S) for x, y in p["pts"]], fill=p["color"],
                width=max(1, int(p["w"] * S)), joint="curve")
    elif p["t"] == "text":
        dr.text((p["x"] * S, p["y"] * S), p["s"], font=font(p["size"], p["weight"] == "bold"),
                fill=p["color"], anchor={"start": "ls", "end": "rs", "middle": "ms"}[p["anchor"]])
img.save(os.path.join(HW, "schematic.png"))

# ------------------------------------------------------------------ export JSON
shapes = []
uid = 0


def gid():
    global uid
    uid += 1
    return f"gge{uid}"


for net, pts in ROUTES.items():
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        shapes.append(f"W~{x1}~{H - y1}~{x2}~{H - y2}~{NET_COLOR[net]}~2~0~none~{gid()}~0~")
for name, y in PINS:
    shapes.append(f"P~{EX2 + 17}~{H - y}~0~#1b2733~8pt~{name}~{gid()}~0~")
for title, y1 in (("J1 AD8232", 110), ("J2 DHT22", 380), ("J4 MAX30102", 540), ("J3 MQ-135", 760)):
    shapes.append(f"T~L~{SX1 + 16}~{H - (y1 + 28)}~0~#1b2733~10pt~{title}~{gid()}~0~")

doc = {
    "head": {
        "docType": "1",
        "editorVersion": "6.5.36",
        "title": "health-monitor-iot",
        "uuid": "8c1d3a52-4f0e-4b7e-9a11-chm000000002",
        "c_para": {"name": "CHM-SCH", "pre": "CHM", "inBom": "true"},
        "x": 0, "y": 0,
    },
    "canvas": f"CA~{W}~{H}~#FFFFFF~yes~#CCCCCC~10~100~100~0",
    "shape": shapes,
    "BBox": {"x": 0, "y": 0, "width": W, "height": H},
    "titleBlock": {
        "title": "Système de santé connecté",
        "rev": "A",
        "company": "USTHB — Faculté de Génie Électrique",
        "comment": "M2 Électronique — Systèmes Embarqués",
    },
    "components": [
        {"ref": "U1", "value": "ESP32 DevKit V1", "footprint": "Module 30 broches"},
        {"ref": "J1", "value": "AD8232", "footprint": "Header 1x06"},
        {"ref": "J2", "value": "DHT22", "footprint": "Header 1x03"},
        {"ref": "J3", "value": "MQ-135", "footprint": "Header 1x04"},
        {"ref": "J4", "value": "MAX30102", "footprint": "Header 1x05"},
        {"ref": "C1", "value": "100 nF", "footprint": "0805"},
        {"ref": "C2", "value": "10 uF", "footprint": "1206"},
    ],
    "nets": ROUTES,
    "note": "Reconstruction : structure documentaire inspirée d'un export EasyEDA Source ; "
            "à réimporter et valider dans l'éditeur avant usage.",
}
json.dump(doc, open(os.path.join(HW, "easyeda", "schematic_source.json"), "w", encoding="utf-8"),
          indent=2, ensure_ascii=False)

print("SVG :", os.path.join(HW, "schematic.svg"))
print("PNG :", os.path.join(HW, "schematic.png"))
