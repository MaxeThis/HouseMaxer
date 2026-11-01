# Prompt: from phone scan to a live 3D home

You need: a LiDAR scan of your home (`.usdz` or `.obj`; we used Scaniverse on
an iPhone Pro), Blender 4 or newer, and the 2D floor plan you already made.

## 1. A clean model from the scan

```text
Here is a LiDAR scan of my home (scan.usdz). Don't use the scan mesh as the
model. Instead:
1. Measure it: wall positions, door and window openings (width, sill, head
   height), ceiling height, and the big furniture.
2. Write apartment_spec.json describing all of that, in the same coordinates as
   tracking/floorplan.json (feet from the top-left, y down; store metres in the
   spec but give me the conversion).
3. Write build_apartment.py that builds a clean Blender model from the spec:
   walls with real openings, doors that can swing (an `open` 0-1 property),
   simple furniture, plain materials. Re-running it rebuilds everything.
4. Render a top-down view and three close-ups so I can check it against the
   scan, and list anything you're unsure of.
```

Then go room by room: "the sofa is 2 ft further from the window", "the bedroom
has a dresser on the left wall". Small fixes, re-run, check the renders.

## 2. Tag the smart devices

```text
Read my Home Assistant devices. For every light, curtain, lock, TV and speaker,
put an Empty in the model where it really is, with custom properties
ha_entities (list of entity IDs) and tracker_ft ([x, y] on my floor plan).
Ask me about any you can't place. Then write devices.json with the same data.
```

## 3. The card

```text
Export the model as a Draco-compressed .glb (drop the scan, cameras and lights).
Then write a three.js Lovelace card that loads it from /local/ and mirrors
Home Assistant live:
- lamps glow in their light's colour and add a real light that only lights
  their own room; give each device its own material copies
- curtains slide, the front door swings from the DoorSense sensor, a ring by
  the lock shows red (unlocked) or green (locked)
- my tracked position as a soft dot; the robot vacuum at its live position
- dollhouse view with orbit controls; walls between the camera and the thing
  I'm looking at fade out
- tap any device for a round pop-up menu of its actions; faint outline on hover
- a 2D/3D toggle that shows the map card instead
Draw every icon and shape yourself; no art copied from games or brands.
Bundle with esbuild into one file. Back up the old bundle before replacing it,
bump the resource version so browsers reload it, and send me a screenshot.
```
