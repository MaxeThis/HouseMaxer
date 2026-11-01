"""Fit the room tracker's radio map from calibration samples.

For each scanner it learns how its reported distance relates to the real one:

    log10(reported_ft) = w0 + w1*log10(r) + w2*walls_crossed
                         + w3 cos(th) + w4 sin(th) + w5 cos(2th) + w6 sin(2th)

r is the 3D distance from the board to the phone, walls_crossed counts walls on
the straight line between them, and th is the bearing (it soaks up an antenna
that hears better one way). The direction terms get a ridge penalty so they
cannot cover for a scanner placed in the wrong spot on the plan.

    python3 fit_radio_map.py floorplan.json samples.jsonl > calib.json

Paste calib.json into your card as CALIB (see map_engine.js). It also prints a
held-out check to stderr: it fits on 4/5 of your spots and reports how far off
the tracker is at the other fifth, five times over.

samples.jsonl rows: {"x": ft, "y": ft, "key": scanner, "d": reported ft}, plus
an optional "pz_m" (phone height). record_spots.py and robot_rows.py write them.

What to look for:
  - slope w1 near 1.0 means the board's readings scale with real distance. Near
    0 means the board barely reacts as you move: check its power, whether it
    sits next to metal, or whether its pin on the plan is wrong.
  - s is the scatter (log10). About 0.2 is normal for cheap ESP32 boards.
"""
import json
import sys
from collections import defaultdict

import numpy as np

from walls import build_cells, crossings, segments, wall_string

FT = 0.3048
PHONE_Z_M = 1.1          # phone in hand; use ~0.8 for a pocket
RIDGE = np.array([0, 0, 0.5, 3, 3, 6, 6.])


def feats(seg, S, x, y, pz=PHONE_Z_M):
    dx = np.asarray(x) - S["x"]; dy = np.asarray(y) - S["y"]
    dz = (S.get("z_m", 1.0) - np.asarray(pz)) / FT
    r = np.maximum(np.sqrt(dx * dx + dy * dy + dz * dz), 1.0)
    th = np.arctan2(dy, dx)
    c = crossings(seg, S["x"], S["y"], x, y)
    return np.column_stack([np.ones_like(r), np.log10(r), c, np.cos(th), np.sin(th), np.cos(2 * th), np.sin(2 * th)])


def fit_one(seg, S, rows):
    x = np.array([q["x"] for q in rows]); y = np.array([q["y"] for q in rows])
    Y = np.log10(np.array([q["d"] for q in rows]))
    pz = np.array([q.get("pz_m", PHONE_Z_M) for q in rows])   # robot runs carry the phone's height
    F = feats(seg, S, x, y, pz)
    R = np.diag(RIDGE) * len(Y) / 100
    w = np.linalg.solve(F.T @ F + R, F.T @ Y)
    return w, float((Y - F @ w).std())


def fit_all(plan, seg, rows_by_key):
    out = {}
    for k, S in plan["scanners"].items():
        rows = [q for q in rows_by_key.get(k, []) if q["d"] > 0]
        if len(rows) < 30:
            print(f"skip {k}: only {len(rows)} readings", file=sys.stderr)
            continue
        w, s = fit_one(seg, S, rows)
        out[k] = {"x": S["x"], "y": S["y"], "z_m": S.get("z_m", 1.0), "w": [round(float(v), 5) for v in w], "s": round(s, 4)}
    return out


def locate(plan, seg, cal, readings, gx, gy, nu=4, infl=1.3):
    """Most likely grid cell for one set of {key: distance} readings (no motion model)."""
    ll = np.zeros_like(gx)
    for k, d in readings.items():
        if k not in cal or not d > 0:
            continue
        S = dict(plan["scanners"][k], **cal[k])
        m = feats(seg, S, gx, gy) @ np.array(S["w"])
        r = (np.log10(d) - m) / (S["s"] * infl)
        ll += -(nu + 1) / 2 * np.log1p(r * r / nu)      # Student-t: robust to a blocked reading
    i = int(np.argmax(ll))
    return gx[i], gy[i]


def main():
    plan = json.load(open(sys.argv[1]))
    rows = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
    seg = segments(build_cells(plan))
    by_key = defaultdict(list)
    for q in rows:
        by_key[q["key"]].append(q)
    cal = fit_all(plan, seg, by_key)

    # Held-out check. Spots are snapped to a 2 ft grid so walk and robot data
    # (where every row is a new spot) group sensibly. Each fold leaves out a
    # fifth of the spots, fits on the rest, and locates the left-out ones.
    spot = lambda q: (round(q["x"] / 2) * 2, round(q["y"] / 2) * 2)
    spots = sorted({spot(q) for q in rows})
    gx, gy = [a.ravel() for a in np.meshgrid(np.arange(0.25, plan["width_ft"], 0.5), np.arange(0.25, plan["height_ft"], 0.5))]
    errs = []
    folds = min(5, len(spots))
    for f in range(folds):
        held = set(spots[f::folds])
        train = defaultdict(list)
        for q in rows:
            if spot(q) not in held:
                train[q["key"]].append(q)
        c = fit_all(plan, seg, train)
        for sp in held:
            here = defaultdict(list)
            for q in rows:
                if spot(q) == sp and q["d"] > 0:
                    here[q["key"]].append(q["d"])
            med = {k: float(np.median(v)) for k, v in here.items()}
            if not med:
                continue
            ex, ey = locate(plan, seg, c, med, gx, gy)
            errs.append(float(np.hypot(ex - sp[0], ey - sp[1])))
    if errs:
        print(f"held-out check: median {np.median(errs):.1f} ft, p90 {np.percentile(errs, 90):.1f} ft over {len(errs)} spots", file=sys.stderr)
    for k, v in cal.items():
        print(f"{k}: slope {v['w'][1]:.2f}  scatter {v['s']:.3f}", file=sys.stderr)

    json.dump({"fit": f"{len(spots)} spots, {len(rows)} readings", "scanners": cal,
               "walls": wall_string(build_cells(plan))}, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
