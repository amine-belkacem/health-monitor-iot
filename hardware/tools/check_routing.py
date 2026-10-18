import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_hardware as gh


def dseg(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


bad = []
for layer, net, w, pts in gh.ROUTES:
    for i in range(len(pts) - 1):
        for p in gh.pads:
            if p["net"] == net:
                continue
            d = dseg((p["x"], p["y"]), pts[i], pts[i + 1])
            if d < 1.2:
                bad.append((layer, net, p["ref"], p["pin"], p["net"], round(d, 2)))

# pastilles sur une même piste (même net) : on vérifie juste qu'aucune piste ne
# traverse la carte hors cadre
print("conflits piste/pastille :", len(bad))
for b in bad:
    print(" ", b)

# collisions entre pistes de la même couche et de nets différents
def seg_int(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    return (ccw(a, c, d) * ccw(b, c, d) < 0) and (ccw(a, b, c) * ccw(a, b, d) < 0)


cross = []
for i, (l1, n1, w1, p1) in enumerate(gh.ROUTES):
    for j, (l2, n2, w2, p2) in enumerate(gh.ROUTES):
        if j <= i or l1 != l2 or n1 == n2:
            continue
        for a, b in zip(p1, p1[1:]):
            for c, d in zip(p2, p2[1:]):
                if seg_int(a, b, c, d):
                    cross.append((n1, n2, l1))
print("croisements même couche :", len(cross))
for c in cross:
    print(" ", c)

# code de sortie non nul si un court-circuit ou un croisement est trouvé (utilisé par la CI)
sys.exit(1 if bad or cross else 0)
