"""Floor-plan walls for the room tracker.

Describe your rooms as boxes and your doorways as gaps, and this builds:
  - WALLS: the half-foot wall-cell string that map_engine.js reads
  - crossings(): how many wall cells a straight line passes through
    (used by fit_radio_map.py)

Units are feet. Origin is the top-left corner of the plan; y grows downward.
Edit floorplan.json (see floorplan.example.json), then:

    pip install numpy
    python3 walls.py floorplan.json        # prints the WALLS string
"""
import json
import sys

import numpy as np


def build_cells(plan):
    cells = set()

    def add(o, c, a, b):
        s = a
        while s < b - 1e-9:
            cells.add((o, round(c, 2), round(s, 2)))
            s += 0.5

    def rm(o, c, a, b):
        for k in [k for k in cells if k[0] == o and abs(k[1] - c) < 1e-6
                  and k[2] >= a - 1e-6 and k[2] + 0.5 <= b + 1e-6]:
            cells.discard(k)

    for r in plan["rooms"]:                       # each room: x, y, w, h
        x, y, w, h = r["x"], r["y"], r["w"], r["h"]
        add("h", y, x, x + w); add("h", y + h, x, x + w)
        add("v", x, y, y + h); add("v", x + w, y, y + h)
    for d in plan.get("doors", []):               # each door: wall 'v' or 'h', at, center, width
        o, at, mid, wd = d["wall"], d["at"], d["center"], d["width"]
        rm(o, at, mid - wd / 2, mid + wd / 2)
    for g in plan.get("openings", []):            # long open spans: wall, at, from, to
        rm(g["wall"], g["at"], g["from"], g["to"])
    W, H = plan["width_ft"], plan["height_ft"]
    # The outside walls never sit between a scanner and the phone, so drop them.
    for k in list(cells):
        o, c, _ = k
        if (o == "h" and c in (0, H)) or (o == "v" and c in (0, W)):
            cells.discard(k)
    return cells


def wall_string(cells):
    return ";".join(f"{o}{c:g},{s:g}" for o, c, s in sorted(cells))


def segments(cells):
    return np.array([[c, s, c, s + .5] if o == "v" else [s, c, s + .5, c] for o, c, s in cells], float)


def crossings(seg, ax, ay, bx, by):
    """Count wall cells crossed by the line A->B (vectorised over arrays of B)."""
    bx = np.atleast_1d(bx).astype(float); by = np.atleast_1d(by).astype(float)
    if len(seg) == 0:
        return np.zeros_like(bx)
    x1, y1, x2, y2 = [seg[:, i][None, :] for i in range(4)]
    dx = (bx - ax)[:, None]; dy = (by - ay)[:, None]
    ex = x2 - x1; ey = y2 - y1
    den = dx * ey - dy * ex
    with np.errstate(divide="ignore", invalid="ignore"):
        t = ((x1 - ax) * ey - (y1 - ay) * ex) / den
        u = ((x1 - ax) * dy - (y1 - ay) * dx) / den
    hit = (np.abs(den) > 1e-12) & (t > 0) & (t < 1) & (u >= 0) & (u < 1)
    return hit.sum(1)


if __name__ == "__main__":
    plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "floorplan.example.json"))
    print(wall_string(build_cells(plan)))
