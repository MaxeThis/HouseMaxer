# 4. Room tracking: where am I?

The house knows which room you are in from your phone's Bluetooth, with no app
to open and no GPS. This drives the walk-up door unlock
([guide 5](05-front-door-lock.md)) and a live map on the dashboard with a dot
that follows you.

```
phone (Bluetooth adverts)
  │
  ├─► ESP32 scanners + Pi radio ─► Home Assistant ─► Bermuda: distance to each scanner
  │                                                     │
  │                                                     ├─► "nearest scanner", "area", home/away
  │                                                     │      (used by the door lock)
  │                                                     │
  │                                                     └─► map engine (tracking/map_engine.js)
  │                                                            uses your floor plan + a calibration
  │                                                            → a dot on the map that doesn't
  │                                                              walk through walls
```

## Step 1: let Home Assistant recognise your iPhone

An iPhone changes its Bluetooth address every few minutes to stop strangers
following it. Home Assistant can still recognise it if it has the phone's
**IRK** (Identity Resolving Key), a secret your phone shares with devices it
pairs with.

1. Get the IRK. The simplest way we know: flash one spare ESP32 with
   [irk-capture](https://github.com/DerekSeaman/irk-capture), pair your phone
   to it from the iPhone's Bluetooth settings, and read the key it shows.
   Then reflash that board with the normal scanner firmware (irk-capture
   can't be a Bluetooth proxy at the same time). Treat this key like a
   password: anyone with it can follow your phone.
2. In Home Assistant add the **Private BLE Device** integration and paste the
   IRK. You get a device for your phone, with a `device_tracker` that says
   home / not_home.

Android phones and watches can use a fixed address instead; check Bermuda's
docs.

## Step 2: Bermuda (distances and rooms)

[Bermuda](https://github.com/agittins/bermuda) (install from HACS) listens
through every Bluetooth proxy and works out how far your phone is from each.
Add the integration, then in its options select your phone. It gives you:

| Entity | What it is | We use it for |
|---|---|---|
| `device_tracker.<phone>` (from Private BLE Device) | home / not_home | away logic |
| `sensor.<phone>_ble_distance` | distance to the nearest scanner (ft) | walk-up unlock |
| `sensor.<phone>_ble_nearest_scanner` | which scanner is closest | away logic |
| `sensor.<phone>_ble_area` | room of the nearest scanner | simple room automations |
| `sensor.<phone>_ble_unfiltered_distance_to_<scanner>` | raw distance to each scanner | the map engine and calibration |

Distances are in feet if your Home Assistant uses US units, metres if metric.
The per-scanner sensors are off by default. Turn them on in the device page
(Entities → show disabled → enable).

**Assign each ESP32 to an Area** (Settings → Devices) and Bermuda's `area`
sensor already gives you room-level presence. Many people can stop here.

## Step 3 (optional): a live map with real calibration

Nearest-scanner is coarse: stand in a doorway and it flips between rooms. We
wanted a dot on a floor plan. The plain approach (trilateration: draw circles
around each scanner, find where they cross) was off by many feet, because walls,
bodies and furniture weaken the signal, and every cheap board hears a bit
differently.

So we **measure** each scanner instead of trusting physics:

1. **Draw the floor plan** as boxes in
   [`tracking/floorplan.example.json`](../tracking/floorplan.example.json):
   rooms, doors, open spans, and where each scanner sits (x, y in feet; z in
   metres). Copy it to `floorplan.json` (git ignores that file, so your layout
   stays private).

2. **Record calibration spots.** Stand still at 15–30 spots spread over every
   room while [`tracking/record_spots.py`](../tracking/record_spots.py) logs
   every scanner's reading for 30 s each.

   ```bash
   export HA_URL=http://homeassistant.local:8123
   export HA_TOKEN=...   # Profile → Security → Long-lived access tokens
   python3 tracking/record_spots.py --prefix sensor.my_phone_ble_unfiltered_distance_to_
   ```

   (We later moved to walking around while tapping our spot on the map, and
   then to taping the phone to the robot vacuum and letting it drive the
   whole floor: see [guide 9](09-roborock-vacuum.md).
   [`tracking/robot_rows.py`](../tracking/robot_rows.py) turns a robot
   recording into the same kind of samples. Same fit, more data.)

3. **Fit a radio map** per scanner:

   ```bash
   pip install numpy
   python3 tracking/fit_radio_map.py tracking/floorplan.json samples.jsonl > calib.json
   ```

   For every scanner it learns
   `log10(reported) = w0 + w1·log10(real distance) + w2·walls crossed + direction terms`.
   It also prints a held-out check: it fits on four fifths of your spots and
   reports how far off the map is at the rest.

4. **Run the engine.** [`tracking/map_engine.js`](../tracking/map_engine.js) is
   plain JavaScript you can drop into any Lovelace card. Each second, feed it
   the latest reading from each scanner. It scores each half-foot square of
   your plan, lets your likely spot move only through doors (never through
   walls), and ignores one wild reading. It returns the cell you are most likely in,
   plus a walking path to animate the dot along.

### What we got

On our first 4-minute calibration walk, tested on parts of the walk the fit
had not seen:

| | Median error | 90% of the time within | Right room |
|---|---|---|---|
| Radio map + wall-aware grid | 4.6 ft | 8.8 ft | 71% |
| ...after fixing one scanner's pin on the map | 4.9 ft | 8.8 ft | 75% |
| ...plus each board's real height | 4.9 ft | 8.8 ft | 76% |

What limits it is noise from the boards (each reading wobbles by about ±60%)
and how much calibration data you have, not the maths. More walks over every
room help most. Two lessons from the numbers:

- **Check each scanner's slope** (`w1` in the fit output). Near 1.0 means its
  readings follow real distance. One of ours read about 0.3: its pin on the map
  was in the wrong place, and the direction terms had been covering for it. One
  read about 0: it was next to metal.
- **Height barely matters.** Moving a board's height from the floor to 8 ft
  changed its fit by under 2%.

## Build the map card with an AI helper

Our dashboard card (floor plan, live dot, device pins you can tap, a
"Calibrate → Walk" mode) is too tied to our home to share as-is. We built it by
describing it to Claude, step by step. The prompts are in
[`prompts/room-tracker-card.md`](../prompts/room-tracker-card.md); give your
AI helper `map_engine.js` and your `calib.json` and it has what it needs.

## Privacy

All of this runs on the Pi. Nothing leaves the house. Keep your IRK, your
`floorplan.json` and your calibration files out of any public repo (this
repo's `.gitignore` already does).

Next: [5. Front door lock](05-front-door-lock.md)
