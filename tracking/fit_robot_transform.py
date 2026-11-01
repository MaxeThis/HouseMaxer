"""Line up the Roborock's map with your floor plan.

The Roborock reports its position in its own map units (mm), with its own
origin and rotation, and its map is often a mirror image of a plan drawn with
y pointing down. This finds the transform

    plan_ft = M @ [raw_x_mm, raw_y_mm] + t

from a few matched points: places where you know both the robot's raw
position and the spot on your plan.

How to collect points (4-6 is plenty, spread far apart):
  1. Drive or send the robot to a spot you can find on your plan (the dock,
     a room corner, a doorway).
  2. In Developer tools -> Actions run roborock.get_vacuum_current_position
     on your vacuum and note x and y.
  3. Write down the same spot in plan feet.

    python3 fit_robot_transform.py points.json

points.json:  [{"raw": [25600, 25600], "plan": [20.0, 10.0]}, ...]

It tries a plain rotation and a mirrored one, keeps the better fit, and prints
M, t, the inverse (for "send the robot here" taps) and the error at each point.
Redo it if the robot ever makes a new map.
"""
import json
import sys

import numpy as np


def fit(raw, plan, mirror):
    """Least-squares similarity (rotation + uniform scale + shift), optionally mirrored."""
    A = raw.copy()
    if mirror:
        A[:, 1] = -A[:, 1]
    ma, mb = A.mean(0), plan.mean(0)
    a, b = A - ma, plan - mb
    U, S, Vt = np.linalg.svd(b.T @ a)
    D = np.diag([1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (a ** 2).sum()
    M = s * R
    if mirror:
        M = M @ np.diag([1, -1])
    t = mb - M @ (ma * (np.array([1, -1]) if mirror else 1))
    res = np.linalg.norm(raw @ M.T + t - plan, axis=1)
    return M, t, res


def main():
    pts = json.load(open(sys.argv[1]))
    raw = np.array([p["raw"] for p in pts], float)
    plan = np.array([p["plan"] for p in pts], float)
    if len(pts) < 2:
        sys.exit("need at least 2 points (3+ to check the fit)")
    best = min((fit(raw, plan, m) + (m,) for m in (False, True)), key=lambda r: r[2].mean())
    M, t, res, mirror = best
    print(json.dumps({
        "note": "plan_ft = M @ [raw_x_mm, raw_y_mm] + t;  raw = Minv @ (plan_ft - t)",
        "mirrored": mirror,
        "M": M.round(9).tolist(),
        "t": t.round(5).tolist(),
        "Minv": np.linalg.inv(M).round(5).tolist(),
        "rotation_deg": round(float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))), 2),
        "error_ft": res.round(2).tolist(),
    }, indent=1))


if __name__ == "__main__":
    main()
