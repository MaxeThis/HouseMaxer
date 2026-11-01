# Prompt: the robot vacuum on your map

You need: the Roborock integration working, and your floor plan.

## 1. Line up the maps

```text
My Roborock is vacuum.<name>. Find the transform from its map coordinates to my
floor plan (feet, y down):
1. Get the robot's map image and its current position from Home Assistant.
2. Register the robot map's walls against my floor plan walls (try both
   mirrored and not). Anchor on the dock position.
3. Report rotation, scale, whether it's mirrored, and the error at 4 points I
   can check by hand. Save M, t and the inverse to roborock_calibration.json.
4. Write the Home Assistant package that updates input_number.roborock_x_ft /
   _y_ft every 5 s while it's cleaning (see
   homeassistant/packages/roborock_live_position.yaml).
```

Check by hand with `tracking/fit_robot_transform.py` and a few measured
points.

## 2. Control it from the map

```text
On the map card, draw the robot at its live position, turning to face the way
it moves. Tap it for a round menu: Clean all, Rooms (pick rooms from the
robot's own room list), Spot (I draw a loop on the map and it cleans inside),
Go to (I tap a spot; use the inverse transform and
roborock.set_vacuum_goto_position), Dock, More (Home Assistant's dialog).
Test "Go to" on the real robot and tell me how far off it stopped.
```

## 3. Calibrate room tracking with the robot

```text
Use custom_components/roborock_pose: arm the calibration recorder, I'll tape
my phone on top of the robot and start a clean. Afterwards pair each new
Bluetooth reading with the robot's position at that moment, refit the radio
map, and show me before/after accuracy. If the watchdog paused the robot,
show me the match values so we can tell a real fall from a false alarm.
```
