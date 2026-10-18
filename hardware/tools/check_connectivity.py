"""
Vérifie que chaque net du PCB relie bien toutes ses pastilles.

check_routing.py ne contrôle que les courts-circuits (piste qui touche une
pastille d'un autre net, croisements). Ce script contrôle l'inverse : les
coupures. Une pastille est reliée à une piste si elle est sur l'un de ses
segments ; deux pistes du même net sont reliées si elles partagent un point.
Les pastilles traversantes relient les deux couches. Le net GND est assuré par
le plan de masse de la couche du bas, il est donc ignoré ici.

Sortie : code 1 si au moins un net est coupé.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_hardware as gh

TOL = 0.05  # mm


def on_segment(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy)) < TOL


def touches(pt, route_pts):
    return any(on_segment(pt, a, b) for a, b in zip(route_pts, route_pts[1:]))


nets = sorted({p["net"] for p in gh.pads} - {"GND", "NC"})
errors = 0
for net in nets:
    pads = [p for p in gh.pads if p["net"] == net]
    routes = [pts for (_, n, _, pts) in gh.ROUTES if n == net]
    # graphe : noeuds = pastilles + pistes, union-find
    parent = list(range(len(pads) + len(routes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    for i, p in enumerate(pads):
        for j, r in enumerate(routes):
            if touches((p["x"], p["y"]), r):
                union(i, len(pads) + j)
    for j, r1 in enumerate(routes):
        for k, r2 in enumerate(routes):
            if k > j and (any(touches(q, r2) for q in r1) or any(touches(q, r1) for q in r2)):
                union(len(pads) + j, len(pads) + k)

    groups = {find(i) for i in range(len(pads))}
    names = ", ".join(f'{p["ref"]}.{p["pin"]}' for p in pads)
    if len(groups) == 1:
        print(f"OK     {net:9s} {names}")
    else:
        errors += 1
        print(f"ECHEC  {net:9s} {len(groups)} morceaux non reliés : {names}")

print(f"\n{len(nets) - errors}/{len(nets)} nets complets")
sys.exit(1 if errors else 0)
