# Prompt: the room-tracker map card

You need: three or more ESP32 Bluetooth proxies, Bermuda set up for your phone
with the per-scanner `unfiltered_distance_to_*` sensors turned on, and a floor
plan as `tracking/floorplan.json` (see `floorplan.example.json`).

## 1. The card

```text
Build a custom Lovelace card, apartment-tracker-card, as one ES module file I
can put in /config/www/ and add as a dashboard resource.

- Draw my floor plan from tracking/floorplan.json as clean SVG: rooms as
  boxes, door gaps, room names. Scale it to the card width; it must work on a
  phone.
- Show each BLE scanner as a small pin. In an "Edit map" mode I can drag pins;
  save positions in Home Assistant per-user storage (frontend/set_user_data)
  so they sync between phone and computer.
- Show a dot for me. Feed tracking/map_engine.js once a second with the
  latest sensor.<phone>_ble_unfiltered_distance_to_* values (skip any older
  than 5 s), and animate the dot along the waypoints advance() returns.
- Device pins: let me place any light, switch, lock, cover or media player on
  the map. Pins glow when the device is on; tap toggles it; long-press opens
  Home Assistant's more-info dialog. Group them in layers I can switch on and
  off with chips under the map.
Make a backup of any file before you overwrite it. When done, open the
dashboard in a browser and send me a screenshot at phone width.
```

## 2. Calibration walk

```text
Add a "Calibrate → Walk" mode to the card. While it runs, I walk around
holding my phone and keep my finger on the map where I am. Record
[ms since start, x_ft, y_ft, finger_down] 10 times a second. When I stop, save
the walk in per-user storage with its start time. Then fetch the history of my
unfiltered distance sensors for that time window, pair each reading with my
position at that moment, and refit the radio map the same way
tracking/fit_radio_map.py does (port it to JS). Show median error and
right-room % before and after, from a 5-fold split of the walk. Only switch
the card to the new fit if it's better.
```

## 3. Check your scanners

```text
From the latest fit, list each scanner's slope (w1) and scatter. Any slope
below 0.5: tell me what is probably wrong (pin in the wrong place on the map,
next to metal, unplugged during the walk) and test it: refit with that
scanner's pin moved to the spot its readings fit best, and report the change.
```
