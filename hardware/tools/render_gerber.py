#!/usr/bin/env python3
"""Rendu PNG de contrôle des Gerbers générés (parseur RS-274X minimal)."""
import os
import re
import sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
GERBER = os.path.join(HW, "gerber")
SCALE = 12          # px / mm
BOARD_H = 75.0

LAYERS = [
    ("chm_bottom_copper.gbl", (46, 92, 128, 255)),
    ("chm_top_copper.gtl", (226, 126, 60, 255)),
    ("chm_top_silkscreen.gto", (241, 246, 252, 255)),
    ("chm_outline.gko", (241, 196, 15, 255)),
]


def parse(path):
    txt = open(path, "r", encoding="ascii").read()
    ap_type, apertures = {}, {}
    m = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", txt)
    div = 10 ** int(m.group(2)) if m else 10 ** 6
    for code, kind, body in re.findall(r"%ADD(\d+)([A-Za-z]+),([^*]*)\*%", txt):
        apertures[int(code)] = [float(v) for v in re.split(r"[X,]", body) if v.strip()]
        ap_type[int(code)] = kind
    cur, polarity = None, "D"
    x = y = 0.0
    shapes = []
    for raw in txt.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("%LPD"):
            polarity = "D"
            continue
        if s.startswith("%LPC"):
            polarity = "C"
            continue
        m = re.match(r"D(\d+)\*$", s)
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(r"X(-?\d+)Y(-?\d+)D0([123])\*$", s)
        if not m:
            continue
        nx, ny = int(m.group(1)) / div, int(m.group(2)) / div
        op = m.group(3)
        if op == "2":
            x, y = nx, ny
        elif op == "1":
            shapes.append(("line", polarity, cur, (x, y), (nx, ny)))
            x, y = nx, ny
        else:
            shapes.append(("flash", polarity, cur, (nx, ny)))
            x, y = nx, ny
    return shapes, apertures, ap_type


def layer_image(shapes, aps, types, color):
    img = Image.new("RGBA", (int(120 * SCALE), int(BOARD_H * SCALE)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    for sh in shapes:
        if sh[0] == "line":
            _, pol, dcode, p1, p2 = sh
            w = (aps.get(dcode) or [0.2])[0]
            c = color if pol == "D" else (0, 0, 0, 0)
            d.line([p1[0] * SCALE, (BOARD_H - p1[1]) * SCALE,
                    p2[0] * SCALE, (BOARD_H - p2[1]) * SCALE],
                   fill=c, width=max(1, int(round(w * SCALE))))
            # bouts arrondis
            r = max(1, w * SCALE / 2)
            for px, py in (p1, p2):
                if pol == "D":
                    d.ellipse([px * SCALE - r, (BOARD_H - py) * SCALE - r,
                               px * SCALE + r, (BOARD_H - py) * SCALE + r], fill=c)
        else:
            _, pol, dcode, p = sh
            params = aps.get(dcode) or [1.8]
            c = color if pol == "D" else (0, 0, 0, 0)
            cx, cy = p[0] * SCALE, (BOARD_H - p[1]) * SCALE
            if types.get(dcode) == "R":
                w, h = (params + params)[:2]
                d.rectangle([cx - w * SCALE / 2, cy - h * SCALE / 2,
                             cx + w * SCALE / 2, cy + h * SCALE / 2], fill=c)
            else:
                r = params[0] * SCALE / 2
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    return img


def main(out):
    img = Image.new("RGBA", (int(120 * SCALE), int(BOARD_H * SCALE)), (12, 17, 22, 255))
    for name, color in LAYERS:
        path = os.path.join(GERBER, name)
        if not os.path.exists(path):
            continue
        shapes, aps, types = parse(path)
        img.alpha_composite(layer_image(shapes, aps, types, color))
    img.convert("RGB").save(out)
    print("preview:", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HW, "preview_pcb.png"))
