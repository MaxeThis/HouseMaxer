"""Record calibration samples for the room tracker.

Stand at a spot, type its floor-plan position, and hold still while this
script logs every scanner's distance to your phone from Home Assistant.
Do 15-30 spots spread over every room (corners, middles, doorways). Hold the
phone the way you normally carry it.

    export HA_URL=http://homeassistant.local:8123
    export HA_TOKEN=...            # Profile -> Security -> Long-lived access token
    python3 record_spots.py --prefix sensor.my_phone_ble_unfiltered_distance_to_ --out samples.jsonl

The prefix is Bermuda's per-scanner distance sensor for your phone, minus the
scanner name. Use the "unfiltered" ones: the fit wants raw readings.
"""
import argparse
import json
import os
import time
import urllib.request


def states(url, token):
    req = urllib.request.Request(url + "/api/states", headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--out", default="samples.jsonl")
    ap.add_argument("--seconds", type=int, default=30, help="how long to hold each spot")
    a = ap.parse_args()
    url, token = os.environ["HA_URL"].rstrip("/"), os.environ["HA_TOKEN"]
    with open(a.out, "a") as f:
        while True:
            s = input("Spot x,y in feet (blank to finish): ").strip()
            if not s:
                break
            x, y = (float(v) for v in s.split(","))
            seen = {}
            t_end = time.time() + a.seconds
            n = 0
            while time.time() < t_end:
                for st in states(url, token):
                    e = st["entity_id"]
                    if not e.startswith(a.prefix):
                        continue
                    key = e[len(a.prefix):]
                    stamp = st["last_updated"]
                    if seen.get(key) == stamp:          # same advert as last poll: skip
                        continue
                    seen[key] = stamp
                    try:
                        d = float(st["state"])
                    except ValueError:
                        continue
                    f.write(json.dumps({"t": time.time(), "x": x, "y": y, "key": key, "d": d}) + "\n")
                    n += 1
                time.sleep(1)
            f.flush()
            print(f"  {n} readings from {len(seen)} scanners")


if __name__ == "__main__":
    main()
