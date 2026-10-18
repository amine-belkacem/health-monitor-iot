#!/usr/bin/env python3
"""
Génère le matériel du projet "health-monitor-iot" :
- Gerbers RS-274X (2 couches) + perçages Excellon, zippés
- Aperçu PNG du PCB
- Fichier source PCB (structure type EasyEDA)
- Pinout / BOM / netlist en CSV

ATTENTION : géométrie reconstruite pour un projet d'archive (voir README).
Le routage est volontairement simple (pas de validation DRC).
"""
import csv
import json
import math
import os
import zipfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)                 # hardware/
ROOT = os.path.dirname(HW)                 # racine projet

BOARD_W, BOARD_H = 120.0, 75.0
EDGE = 1.0

# --------------------------------------------------------------------------
# Géométrie
# --------------------------------------------------------------------------
PITCH = 2.54
Y0 = 54.78          # première broche (haut) de l'ESP32
LEFT_X, RIGHT_X = 50.0, 101.0
BODY = (52.2, 20.8, 98.8, 53.8)   # x1, y1, x2, y2

LEFT_PINS = ["EN", "VP36", "VN39", "34", "35", "32", "33", "25", "26", "27",
             "14", "12", "13", "GND", "VIN"]
RIGHT_PINS = ["3V3", "GND", "15", "2", "4", "16", "17", "5", "18", "19", "21",
              "RX0", "TX0", "22", "23"]

NET_OF_PIN = {
    "34": "ECG_OUT", "35": "MQ_AOUT", "32": "LO_PLUS", "33": "LO_MINUS",
    "27": "DHT_DATA", "21": "SDA", "22": "SCL",
    "3V3": "3V3", "GND": "GND", "VIN": "5V",
}

pads = []      # dict(ref, pin, x, y, net, drill, shape, label)


def pad(ref, pin, x, y, net, drill=1.0, shape="circle", label=None):
    pads.append(dict(ref=ref, pin=pin, x=round(x, 3), y=round(y, 3), net=net,
                     drill=drill, shape=shape, label=label or pin))


def build_pads():
    for i, name in enumerate(LEFT_PINS):
        pad("U1", name, LEFT_X, Y0 - i * PITCH, NET_OF_PIN.get(name, "NC"))
    for i, name in enumerate(RIGHT_PINS):
        pad("U1", name, RIGHT_X, Y0 - i * PITCH, NET_OF_PIN.get(name, "NC"))

    # J1 : module ECG AD8232 (GND, 3V3, OUTPUT, LO-, LO+, SDN)
    j1 = [("1", "GND", "GND"), ("2", "3V3", "3V3"), ("3", "OUTPUT", "ECG_OUT"),
          ("4", "LO-", "LO_MINUS"), ("5", "LO+", "LO_PLUS"), ("6", "SDN", "3V3")]
    for k, (p, lbl, net) in enumerate(j1):
        pad("J1", p, 16.0, 49.70 - k * PITCH, net, label=lbl)

    # J2 : DHT22 (VCC, DATA, GND)
    for k, (p, lbl, net) in enumerate([("1", "VCC", "3V3"), ("2", "DATA", "DHT_DATA"),
                                       ("3", "GND", "GND")]):
        pad("J2", p, 16.0, 31.92 - k * PITCH, net, label=lbl)

    # J3 : MQ-135 (VCC, GND, AOUT, DOUT)
    for k, (p, lbl, net) in enumerate([("1", "VCC", "5V"), ("2", "GND", "GND"),
                                       ("3", "AOUT", "MQ_AOUT"), ("4", "DOUT", "NC")]):
        pad("J3", p, 16.0, 21.76 - k * PITCH, net, label=lbl)

    # J4 : MAX30102 (VIN, GND, SDA, SCL, INT)
    for k, (p, lbl, net) in enumerate([("1", "VIN", "3V3"), ("2", "GND", "GND"),
                                       ("3", "SDA", "SDA"), ("4", "SCL", "SCL"),
                                       ("5", "INT", "NC")]):
        pad("J4", p, 112.0, 34.46 - k * PITCH, net, label=lbl)

    # Découplage
    pad("C1", "1", 103.0, 60.5, "3V3", label="100nF")
    pad("C1", "2", 105.54, 60.5, "GND", label="100nF")
    pad("C2", "1", 110.0, 48.54, "3V3", label="10uF")
    pad("C2", "2", 110.0, 46.0, "GND", label="10uF")


build_pads()

MOUNT = [(5.0, 5.0), (115.0, 5.0), (5.0, 70.0), (115.0, 70.0)]

# Routes : (couche, net, largeur, [(x, y), ...])
ROUTES = [
    # --- signaux, couche TOP ---
    ("top", "ECG_OUT", 0.30, [(16.0, 44.62), (22.0, 44.62), (22.0, 47.16), (50.0, 47.16)]),
    ("top", "DHT_DATA", 0.30, [(16.0, 29.38), (20.0, 29.38), (20.0, 31.92), (50.0, 31.92)]),
    # --- alimentation 3V3 (top) ---
    ("top", "3V3", 0.50, [(101.0, 54.78), (106.0, 54.78), (106.0, 58.50),
                          (12.0, 58.50), (12.0, 47.16), (16.0, 47.16)]),
    ("top", "3V3", 0.50, [(12.0, 47.16), (12.0, 37.00), (16.0, 37.00)]),        # SDN
    ("top", "3V3", 0.50, [(12.0, 37.00), (12.0, 31.92), (16.0, 31.92)]),        # J2 VCC
    ("top", "3V3", 0.50, [(103.0, 58.50), (103.0, 60.50)]),                     # C1
    ("top", "3V3", 0.50, [(106.0, 48.54), (110.0, 48.54)]),                     # C2
    ("top", "3V3", 0.50, [(106.0, 58.50), (106.0, 34.46), (112.0, 34.46)]),     # J4 VIN
    # --- 5V (top) ---
    ("top", "5V", 0.50, [(50.0, 19.22), (50.0, 12.0), (12.0, 12.0),
                         (12.0, 21.76), (16.0, 21.76)]),
    # --- MQ-135 AOUT : contourne par le bas (bottom) ---
    ("bottom", "MQ_AOUT", 0.40, [(16.0, 16.68), (8.0, 16.68), (8.0, 52.00),
                                 (46.0, 52.00), (46.0, 44.62), (50.0, 44.62)]),
    # --- détection électrodes AD8232 : LO+ et LO- se croisent (J1.5 -> GPIO32,
    #     J1.4 -> GPIO33), donc LO+ en TOP et LO- en BOTTOM ---
    ("top", "LO_PLUS", 0.30, [(16.0, 39.54), (24.0, 39.54), (24.0, 42.08), (50.0, 42.08)]),
    ("bottom", "LO_MINUS", 0.40, [(16.0, 42.08), (30.0, 42.08), (30.0, 39.54), (50.0, 39.54)]),
    # --- bus I2C du MAX30102 (GPIO21 / GPIO22 -> J4.3 / J4.4) ---
    ("top", "SDA", 0.30, [(101.0, 29.38), (112.0, 29.38)]),
    ("top", "SCL", 0.30, [(101.0, 21.76), (108.0, 21.76), (108.0, 26.84), (112.0, 26.84)]),
]


# --------------------------------------------------------------------------
# Police "stroke" minimaliste pour la sérigraphie
# --------------------------------------------------------------------------
FONT = {
    "A": [[(0, 0), (2.5, 7), (5, 0)], [(1.1, 2.6), (3.9, 2.6)]],
    "B": [[(0, 0), (0, 7), (3.5, 7), (5, 6.1), (5, 4.2), (3.5, 3.5), (0, 3.5)],
          [(3.5, 3.5), (5, 2.6), (5, 0.9), (3.5, 0), (0, 0)]],
    "C": [[(5, 1.3), (3.8, 0), (1.3, 0), (0, 1.3), (0, 5.7), (1.3, 7), (3.8, 7), (5, 5.7)]],
    "D": [[(0, 0), (0, 7), (3.2, 7), (5, 5.2), (5, 1.8), (3.2, 0), (0, 0)]],
    "E": [[(5, 7), (0, 7), (0, 0), (5, 0)], [(0, 3.6), (3.7, 3.6)]],
    "G": [[(5, 1.3), (3.8, 0), (1.3, 0), (0, 1.3), (0, 5.7), (1.3, 7), (3.8, 7), (5, 5.7),
           (5, 3.9), (2.8, 3.9)]],
    "F": [[(0, 0), (0, 7), (5, 7)], [(0, 3.4), (3.4, 3.4)]],
    "J": [[(5, 7), (5, 1.2), (3.8, 0), (1.4, 0), (0, 1.2)]],
    "K": [[(0, 0), (0, 7)], [(5, 7), (0, 3.2)], [(1.6, 4.3), (5, 0)]],
    "L": [[(0, 7), (0, 0), (5, 0)]],
    "Z": [[(0, 7), (5, 7), (0, 0), (5, 0)]],
    "H": [[(0, 0), (0, 7)], [(5, 0), (5, 7)], [(0, 3.5), (5, 3.5)]],
    "I": [[(1.2, 0), (3.8, 0)], [(2.5, 0), (2.5, 7)], [(1.2, 7), (3.8, 7)]],
    "M": [[(0, 0), (0, 7), (2.5, 3.6), (5, 7), (5, 0)]],
    "N": [[(0, 0), (0, 7), (5, 0), (5, 7)]],
    "O": [[(1.4, 0), (0, 1.4), (0, 5.6), (1.4, 7), (3.6, 7), (5, 5.6), (5, 1.4),
           (3.6, 0), (1.4, 0)]],
    "P": [[(0, 0), (0, 7), (3.6, 7), (5, 5.8), (5, 4.2), (3.6, 3.2), (0, 3.2)]],
    "Q": [[(1.4, 0), (0, 1.4), (0, 5.6), (1.4, 7), (3.6, 7), (5, 5.6), (5, 1.4),
           (3.6, 0), (1.4, 0)], [(3.1, 1.9), (5.1, -0.3)]],
    "R": [[(0, 0), (0, 7), (3.6, 7), (5, 5.8), (5, 4.2), (3.6, 3.2), (0, 3.2)],
          [(3.0, 3.2), (5, 0)]],
    "S": [[(5, 6.1), (3.6, 7), (1.4, 7), (0, 5.7), (0, 4.4), (1.3, 3.4), (3.7, 3.2),
           (5, 2.3), (5, 1.2), (3.6, 0), (1.4, 0), (0, 0.9)]],
    "T": [[(0, 7), (5, 7)], [(2.5, 7), (2.5, 0)]],
    "U": [[(0, 7), (0, 1.4), (1.4, 0), (3.6, 0), (5, 1.4), (5, 7)]],
    "V": [[(0, 7), (2.5, 0), (5, 7)]],
    "W": [[(0, 7), (1.0, 0), (2.5, 4.0), (4.0, 0), (5, 7)]],
    "X": [[(0, 0), (5, 7)], [(0, 7), (5, 0)]],
    "Y": [[(0, 7), (2.5, 3.5), (5, 7)], [(2.5, 3.5), (2.5, 0)]],
    "0": [[(1.4, 0), (0, 1.4), (0, 5.6), (1.4, 7), (3.6, 7), (5, 5.6), (5, 1.4),
           (3.6, 0), (1.4, 0)], [(0.4, 1.4), (4.6, 5.6)]],
    "1": [[(1.4, 5.6), (2.5, 7), (2.5, 0)], [(1.2, 0), (3.8, 0)]],
    "2": [[(0, 5.6), (1.4, 7), (3.6, 7), (5, 5.6), (5, 4.2), (0, 0), (5, 0)]],
    "3": [[(0, 6.0), (1.4, 7), (3.6, 7), (5, 6.0), (5, 4.2), (3.2, 3.6), (5, 3.0),
           (5, 1.0), (3.6, 0), (1.4, 0), (0, 1.0)]],
    "4": [[(3.6, 0), (3.6, 7), (0, 2.2), (5, 2.2)]],
    "5": [[(5, 7), (0, 7), (0, 4.0), (3.4, 4.0), (5, 3.0), (5, 1.0), (3.6, 0),
           (1.4, 0), (0, 1.0)]],
    "6": [[(5, 6.0), (3.6, 7), (1.4, 7), (0, 5.6), (0, 1.4), (1.4, 0), (3.6, 0),
           (5, 1.4), (5, 3.0), (3.6, 4.2), (0, 4.2)]],
    "7": [[(0, 7), (5, 7), (2.0, 0)]],
    "8": [[(1.2, 3.5), (0, 4.5), (0, 6.0), (1.4, 7), (3.6, 7), (5, 6.0), (5, 4.5),
           (3.8, 3.5), (1.2, 3.5), (0, 2.5), (0, 1.0), (1.4, 0), (3.6, 0), (5, 1.0),
           (5, 2.5), (3.8, 3.5)]],
    "9": [[(0, 1.0), (1.4, 0), (3.6, 0), (5, 1.4), (5, 5.6), (3.6, 7), (1.4, 7),
           (0, 5.6), (0, 4.0), (1.4, 2.8), (5, 2.8)]],
    "-": [[(0, 3.5), (5, 3.5)]],
    ".": [[(2.2, 0), (2.7, 0)]],
    "+": [[(2.5, 1.6), (2.5, 5.4)], [(0.6, 3.5), (4.4, 3.5)]],
    "/": [[(0, 0), (5, 7)]],
    " ": [],
}


def text_polys(x, y, height, s, spacing=1.35):
    """Retourne des polylignes (mm) pour un texte, origine en bas à gauche."""
    polys, cx = [], x
    sc = height / 7.0
    for ch in s.upper():
        for stroke in FONT.get(ch, []):
            polys.append([(cx + px * sc, y + py * sc) for px, py in stroke])
        cx += 5 * sc + spacing * sc
    return polys


def text_width(height, s, spacing=1.35):
    sc = height / 7.0
    return len(s) * (5 * sc + spacing * sc)


# --------------------------------------------------------------------------
# Écriture Gerber
# --------------------------------------------------------------------------
def g(v):
    return str(int(round(v * 1_000_000)))


class Gerber:
    def __init__(self, function):
        self.head = [
            "%TF.GenerationSoftware,health-monitor-iot,reconstruction,1.0*%",
            f"%TF.FileFunction,{function}*%",
            "%FSLAX46Y46*%",
            "%MOMM*%",
        ]
        self.apertures = {}
        self.next_d = 10
        self.body = []
        self.cur = None
        self.polarity = "D"

    def ap(self, kind, *params):
        key = (kind,) + tuple(params)
        if key not in self.apertures:
            self.apertures[key] = self.next_d
            self.next_d += 1
        return self.apertures[key]

    def set_ap(self, d):
        if self.cur != d:
            self.body.append(f"D{d}*")
            self.cur = d

    def polarity_dark(self):
        if self.polarity != "D":
            self.body.append("%LPD*%")
            self.polarity = "D"

    def polarity_clear(self):
        if self.polarity != "C":
            self.body.append("%LPC*%")
            self.polarity = "C"

    def flash(self, x, y, d):
        self.set_ap(d)
        self.body.append(f"X{g(x)}Y{g(y)}D03*")

    def line(self, pts, d):
        self.set_ap(d)
        x0, y0 = pts[0]
        self.body.append(f"X{g(x0)}Y{g(y0)}D02*")
        for x, y in pts[1:]:
            self.body.append(f"X{g(x)}Y{g(y)}D01*")

    def save(self, path):
        out = ["G04 health-monitor-iot - generated*"]
        out += self.head
        for (kind, *params), d in self.apertures.items():
            sep = "X" if kind == "R" else ","
            out.append(f"%ADD{d}{kind},{sep.join(format(p, '.6f') for p in params)}*%")
        out.append("G01*")
        out += self.body
        out.append("M02*")
        with open(path, "w", encoding="ascii", newline="\n") as f:
            f.write("\n".join(out) + "\n")


def write_gerbers(outdir):
    os.makedirs(outdir, exist_ok=True)
    files = {}

    # --- TOP copper : pads + pistes ---
    top = Gerber("Copper,L1,Top")
    d_trace = top.ap("C", 0.30)
    d_trace5 = top.ap("C", 0.50)
    d_trace4 = top.ap("C", 0.40)
    d_pad = top.ap("C", 1.80)
    d_pad_sq = top.ap("R", 1.80, 1.80)
    for p in pads:
        top.flash(p["x"], p["y"], d_pad_sq if p["pin"] == "1" else d_pad)
    widths = {0.30: d_trace, 0.40: d_trace4, 0.50: d_trace5}
    for layer, net, w, pts in ROUTES:
        if layer == "top":
            top.line(pts, widths[w])
    top.save(os.path.join(outdir, "chm_top_copper.gtl"))
    files["gtl"] = "chm_top_copper.gtl"

    # --- BOTTOM copper : plan de masse + piste MQ_AOUT ---
    bot = Gerber("Copper,L2,Bot")
    d_plane = bot.ap("R", BOARD_W - 2 * EDGE, BOARD_H - 2 * EDGE)
    d_clear = bot.ap("C", 2.40)
    d_clear_trace = bot.ap("C", 2.20)
    d_trace = bot.ap("C", 0.40)
    d_gnd = bot.ap("C", 1.80)
    bot.flash(BOARD_W / 2, BOARD_H / 2, d_plane)
    # dégagement autour de la piste MQ_AOUT
    for layer, net, w, pts in ROUTES:
        if layer == "bottom":
            bot.polarity_clear()
            bot.line(pts, d_clear_trace)
            bot.polarity_dark()
    # dégagement autour des pastilles non-GND
    bot.polarity_clear()
    for p in pads:
        if p["net"] != "GND":
            bot.flash(p["x"], p["y"], d_clear)
    bot.polarity_dark()
    for layer, net, w, pts in ROUTES:
        if layer == "bottom":
            bot.line(pts, d_trace)
    for p in pads:
        if p["net"] == "GND":
            bot.flash(p["x"], p["y"], d_gnd)
    bot.save(os.path.join(outdir, "chm_bottom_copper.gbl"))
    files["gbl"] = "chm_bottom_copper.gbl"

    # --- masques ---
    for side, name in (("top", "chm_top_mask.gts"), ("bottom", "chm_bottom_mask.gbs")):
        m = Gerber(f"Soldermask,{'L1,Top' if side == 'top' else 'L2,Bot'}")
        d_open = m.ap("C", 2.30)
        d_open_sq = m.ap("R", 2.30, 2.30)
        for p in pads:
            m.flash(p["x"], p["y"], d_open_sq if p["pin"] == "1" else d_open)
        for (x, y) in MOUNT:
            m.flash(x, y, d_open)
        m.save(os.path.join(outdir, name))
        files["gts" if side == "top" else "gbs"] = name

    # --- sérigraphie dessus ---
    sil = Gerber("Legend,L1,Top")
    d_silk = sil.ap("C", 0.15)
    d_silk2 = sil.ap("C", 0.20)
    # contour carte
    sil.line([(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)], d_silk2)
    # contour module ESP32
    x1, y1, x2, y2 = BODY
    sil.line([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)], d_silk)
    # encoches connecteurs
    for (ref, ytop, n) in (("J1", 49.70, 6), ("J2", 31.92, 3), ("J3", 21.76, 4)):
        ybot = ytop - (n - 1) * PITCH
        sil.line([(11.5, ybot - 1.2), (20.5, ybot - 1.2), (20.5, ytop + 1.2), (11.5, ytop + 1.2),
                  (11.5, ybot - 1.2)], d_silk)
    sil.line([(107.5, 21.6), (116.5, 21.6), (116.5, 35.8), (107.5, 35.8), (107.5, 21.6)], d_silk)
    # condensateurs
    for cx, cy in ((104.27, 60.5), (110.0, 47.27)):
        sil.line([(cx - 2.2, cy), (cx + 2.2, cy)], d_silk)
        sil.flash(cx, cy, sil.ap("C", 0.15))
    # repère broche 1
    sil.flash(46.6, 47.16, sil.ap("C", 0.45))
    # textes
    labels = [
        (23.0, 53.9, 1.2, "J1 ECG"),
        (22.8, 33.9, 1.0, "J2 DHT22"),
        (22.8, 23.8, 1.0, "J3 MQ-135"),
        (106.0, 36.4, 1.0, "J4 MAX30102"),
        (54.0, 55.6, 1.5, "ESP32 DEVKIT V1"),
        (30.0, 70.2, 2.0, "CONNECTED HEALTH MONITOR"),
        (30.0, 67.4, 1.1, "USTHB - FGE - M2 SE - REV A"),
        (101.5, 64.0, 1.0, "CHM"),
    ]
    for tx, ty, h, s in labels:
        for poly in text_polys(tx, ty, h, s):
            sil.line(poly, d_silk)
    # croix de perçage
    for (mx, my) in MOUNT:
        sil.line([(mx - 1.2, my), (mx + 1.2, my)], d_silk)
        sil.line([(mx, my - 1.2), (mx, my + 1.2)], d_silk)
    sil.save(os.path.join(outdir, "chm_top_silkscreen.gto"))
    files["gto"] = "chm_top_silkscreen.gto"

    # --- contour ---
    out = Gerber("Profile,NP")
    d_edge = out.ap("C", 0.15)
    out.line([(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_H), (0, BOARD_H), (0, 0)], d_edge)
    out.save(os.path.join(outdir, "chm_outline.gko"))
    files["gko"] = "chm_outline.gko"

    # --- perçages Excellon ---
    drl = [
        "M48",
        "; health-monitor-iot - drill file",
        "FMAT,2",
        "METRIC,TZ",
        "T1C1.000",
        "T2C3.200",
        "%",
        "G90",
        "G05",
        "T1",
    ]
    for p in pads:
        drl.append(f"X{p['x']:.3f}Y{p['y']:.3f}")
    drl.append("T2")
    for (mx, my) in MOUNT:
        drl.append(f"X{mx:.3f}Y{my:.3f}")
    drl += ["T0", "M30"]
    with open(os.path.join(outdir, "chm_drill.drl"), "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(drl) + "\n")
    files["drl"] = "chm_drill.drl"

    # --- zip ---
    zpath = os.path.join(outdir, f"health-monitor-iot-gerber-{date.today():%Y%m%d}.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for name in files.values():
            z.write(os.path.join(outdir, name), arcname=name)
        z.writestr("readme_gerber.txt",
                   "Gerbers RS-274X, 2 couches, 120 x 75 mm.\n"
                   "Piste MQ_AOUT sur la couche bottom (plan de masse decoupe).\n"
                   "Fichier de percage : Excellon, mm.\n"
                   "Reconstruction : a verifier avant toute fabrication.\n")
    return files, zpath


# --------------------------------------------------------------------------
# Export JSON "type EasyEDA" (structure documentaire, non validée par l'EDI)
# --------------------------------------------------------------------------
def write_pcb_json(path, files):
    tracks = []
    for layer, net, w, pts in ROUTES:
        tracks.append({"net": net, "layer": "top" if layer == "top" else "bottom",
                       "width": w, "points": [[x, y] for x, y in pts]})
    doc = {
        "head": {
            "docType": "3",
            "editorVersion": "6.5.36",
            "title": "health-monitor-iot",
            "uuid": "2f4c9c1e-8b7d-4b5a-9d0e-chm000000001",
            "c_para": {"name": "CHM-PCB", "pre": "CHM", "inBom": "true"},
            "x": 0, "y": 0,
        },
        "canvas": f"CA~{BOARD_W}~{BOARD_H}~#101820~yes~#3A4A5A~10~100~100~0",
        "BBox": {"x": 0, "y": 0, "width": BOARD_W, "height": BOARD_H},
        "layers": ["top", "bottom"],
        "board": {"width": BOARD_W, "height": BOARD_H, "thickness": 1.6,
                  "material": "FR-4", "copper_weight": "1 oz"},
        "footprints": [],
        "pads": [{"ref": p["ref"], "pin": p["pin"], "x": p["x"], "y": p["y"],
                  "net": p["net"], "drill": p["drill"],
                  "shape": "rect" if p["pin"] == "1" else "circle",
                  "size": [1.8, 1.8]} for p in pads],
        "tracks": tracks,
        "silkscreen": {"labels": [
            {"text": "J1 ECG", "x": 23.0, "y": 53.9, "size": 1.2},
            {"text": "J2 DHT22", "x": 22.8, "y": 33.9, "size": 1.0},
            {"text": "J3 MQ-135", "x": 22.8, "y": 23.8, "size": 1.0},
            {"text": "J4 MAX30102", "x": 106.0, "y": 36.4, "size": 1.0},
            {"text": "ESP32 DEVKIT V1", "x": 54.0, "y": 55.6, "size": 1.5},
            {"text": "CONNECTED HEALTH MONITOR", "x": 30.0, "y": 70.2, "size": 2.0},
        ]},
        "drill": {"tool_1": 1.0, "tool_2": 3.2},
        "manufacturing": {"files": files,
                          "note": "Reconstruction - routage simplifie, non valide DRC"},
    }
    for ref, kind, x, y in (("U1", "ESP32 DevKit V1", 52.2, 20.8),
                            ("J1", "Header 1x06 2.54", 11.5, 37.0),
                            ("J2", "Header 1x03 2.54", 11.5, 26.8),
                            ("J3", "Header 1x04 2.54", 11.5, 14.1),
                            ("J4", "Header 1x05 2.54", 107.5, 22.2),
                            ("C1", "100 nF 0805", 103.0, 60.5),
                            ("C2", "10 uF 1206", 110.0, 48.5)):
        doc["footprints"].append({"ref": ref, "name": kind, "x": x, "y": y,
                                  "rotation": 0, "layer": "top"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        w.writerows(rows)


def main():
    files, zpath = write_gerbers(os.path.join(HW, "gerber"))
    write_pcb_json(os.path.join(HW, "easyeda", "pcb_source.json"), files)

    write_csv(os.path.join(HW, "pinout.csv"),
              ["Composant", "Broche composant", "Signal", "Net", "Broche ESP32", "GPIO"],
              [["AD8232", "OUTPUT", "Signal ECG (analogique)", "ECG_OUT", "34", "GPIO34"],
               ["AD8232", "LO+", "Déconnexion électrode +", "LO_PLUS", "32", "GPIO32"],
               ["AD8232", "LO-", "Déconnexion électrode -", "LO_MINUS", "33", "GPIO33"],
               ["AD8232", "3.3V", "Alimentation", "3V3", "3V3", "-"],
               ["AD8232", "GND", "Masse", "GND", "GND", "-"],
               ["AD8232", "SDN", "Shutdown (tiré à 3V3)", "3V3", "3V3", "-"],
               ["DHT22", "VCC", "Alimentation", "3V3", "3V3", "-"],
               ["DHT22", "DATA", "One-Wire", "DHT_DATA", "27", "GPIO27"],
               ["DHT22", "GND", "Masse", "GND", "GND", "-"],
               ["MAX30102", "VIN", "Alimentation", "3V3", "3V3", "-"],
               ["MAX30102", "GND", "Masse", "GND", "GND", "-"],
               ["MAX30102", "SDA", "I2C données", "SDA", "21", "GPIO21"],
               ["MAX30102", "SCL", "I2C horloge", "SCL", "22", "GPIO22"],
               ["MAX30102", "INT", "Interruption (non utilisée)", "NC", "-", "-"],
               ["MQ-135", "VCC", "Alimentation 5 V", "5V", "VIN", "-"],
               ["MQ-135", "GND", "Masse", "GND", "GND", "-"],
               ["MQ-135", "AOUT", "Sortie analogique", "MQ_AOUT", "35", "GPIO35"],
               ["MQ-135", "DOUT", "Sortie numérique (non utilisée)", "NC", "-", "-"]])

    write_csv(os.path.join(HW, "bom.csv"),
              ["Référence", "Désignation", "Valeur", "Boîtier", "Quantité", "Rôle"],
              [["U1", "Module ESP32 DevKit V1", "ESP32-WROOM-32", "Module 30 broches", 1,
                "Acquisition, Wi-Fi, HTTP"],
               ["J1", "Connecteur mâle", "1x06 2.54 mm", "THT", 1, "Module ECG AD8232"],
               ["J2", "Connecteur mâle", "1x03 2.54 mm", "THT", 1, "DHT22"],
               ["J3", "Connecteur mâle", "1x04 2.54 mm", "THT", 1, "MQ-135"],
               ["J4", "Connecteur mâle", "1x05 2.54 mm", "THT", 1, "MAX30102"],
               ["C1", "Condensateur céramique", "100 nF", "0805", 1, "Découplage 3V3"],
               ["C2", "Condensateur polarisé", "10 uF", "1206", 1, "Réservoir 3V3"],
               ["-", "Entretoises + vis M3", "3.2 mm", "-", 4, "Fixation"]])

    write_csv(os.path.join(HW, "netlist.csv"),
              ["Net", "Broches"],
              [["GND", "U1 GND (x2), J1.1, J2.3, J3.2, J4.2, C1.2, C2.2"],
               ["3V3", "U1 3V3, J1.2, J1.6 (SDN), J2.1, J4.1, C1.1, C2.1"],
               ["5V", "U1 VIN, J3.1"],
               ["ECG_OUT", "U1 34, J1.3"],
               ["LO_PLUS", "U1 32, J1.5"],
               ["LO_MINUS", "U1 33, J1.4"],
               ["DHT_DATA", "U1 27, J2.2"],
               ["SDA", "U1 21, J4.3"],
               ["SCL", "U1 22, J4.4"],
               ["MQ_AOUT", "U1 35, J3.3"]])

    print("Gerbers :", ", ".join(files.values()))
    print("ZIP     :", os.path.basename(zpath))
    print("Pads    :", len(pads), "| routes :", len(ROUTES))


if __name__ == "__main__":
    main()





