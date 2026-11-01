"""Turn a robot calibration recording into rows for fit_radio_map.py.

custom_components/roborock_pose records one line per second while the robot
cleans with your phone taped on top: the robot's pose (map mm) and every
Bluetooth distance sensor with its own update time. This pairs each *new*
reading with where the robot was at that moment, converts it to plan feet with
the transform from fit_robot_transform.py, and drops stretches the watchdog
flagged as "phone fell off".

Copy the recording off Home Assistant first (it is in /config/roborock_calib/,
or use the roborock_pose.calib_get action), then:

    python3 robot_rows.py 1793543206165.jsonl transform.json >> samples.jsonl
"""
import json
import sys

PHONE_ON_ROBOT_M = 0.12   # phone height when it lies on top of the robot
POSE_LAG = 0.3            # a pose shows up about this long after the robot was there
MAX_AGE = 1.5             # ignore readings older than this when first seen


def main():
    lines = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    xf = json.load(open(sys.argv[2]))
    M, t = xf["M"], xf["t"]
    lost = [(e["from"], e["t"]) for e in lines if e.get("ev") == "lost"]
    ticks = [e for e in lines if "t1" in e]

    # pose timeline in plan feet
    poses = []
    for e in ticks:
        if e.get("p") and e.get("s") == "cleaning":
            x, y = e["p"][0], e["p"][1]
            poses.append((e["t1"] - POSE_LAG, M[0][0] * x + M[0][1] * y + t[0], M[1][0] * x + M[1][1] * y + t[1]))

    def where(ts):
        if not poses or ts < poses[0][0] or ts > poses[-1][0]:
            return None
        for (ta, xa, ya), (tb, xb, yb) in zip(poses, poses[1:]):
            if ta <= ts <= tb:
                if tb - ta > 3:          # gap mid-move: don't guess
                    return None
                u = (ts - ta) / (tb - ta) if tb > ta else 0
                return xa + (xb - xa) * u, ya + (yb - ya) * u
        return None

    seen, n = {}, 0
    for e in ticks:
        if e.get("s") != "cleaning":
            continue
        for key, (d, stamp) in (e.get("b") or {}).items():
            if seen.get(key) == stamp:
                continue                  # same advert as last tick
            seen[key] = stamp
            if e["t1"] - stamp > MAX_AGE or d <= 0:
                continue
            if any(a <= stamp <= b for a, b in lost):
                continue
            p = where(stamp)
            if p is None:
                continue
            print(json.dumps({"t": stamp, "x": round(p[0], 2), "y": round(p[1], 2), "key": key, "d": d, "pz_m": PHONE_ON_ROBOT_M}))
            n += 1
    print(f"{n} rows from {len(ticks)} ticks", file=sys.stderr)


if __name__ == "__main__":
    main()
