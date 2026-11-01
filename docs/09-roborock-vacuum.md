# 9. Robot vacuum: Roborock Qrevo Plus

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

The Roborock Qrevo Plus vacuums and mops, then empties itself and washes its
mop pads at the dock.

- [Roborock Qrevo Plus (Amazon Renewed)](https://www.amazon.com/roborock_qrevo_plus_renewed/dp/B0FMKBBFLR?tag=maxestmax-20)
- [Roborock Qrevo Plus (main listing)](https://www.amazon.com/roborock_qrevo_plus/dp/B0D2Y8MY5T?tag=maxestmax-20); when we
  checked it had only "used, like new" stock

**We bought ours refurbished**, and for a robot vacuum we would again: it is
the priciest thing on this list, refurbished units come checked and with a
warranty, and the parts that wear out (brushes, filters, mop pads, dust bags)
are cheap to replace anyway.

## Hook it up

1. Set it up in the **Roborock app** first and let it map your home.
2. In Home Assistant add the **Roborock** integration and sign in with your
   Roborock account.
   - **US users:** older Home Assistant versions only looked for your account
     on Roborock's European server and said "invalid email". Update Home
     Assistant to a current version first.
3. You get `vacuum.<name>`, the live map as an image, battery, cleaning
   progress, the dock's switches, and how worn each part is.

**Network:** our robot lives on the 2.4 GHz guest Wi-Fi, with ASUS's **Access
Intranet** switched on so Home Assistant can reach it on the local network
([guide 2](02-network-asus-router.md)).

## The robot on your own floor plan

Home Assistant can ask the robot where it is
(`roborock.get_vacuum_current_position`), but the answer is in the robot's own
map: millimetres, its own starting point, its own rotation, and often a mirror
image of a plan drawn with y pointing down. To show it on your floor plan you
need the transform between the two.

1. Collect 4–6 matching points: put the robot somewhere you can find on your
   plan (the dock, a room corner), run `roborock.get_vacuum_current_position`
   in Developer tools → Actions, and note both positions.
2. Run [`tracking/fit_robot_transform.py`](../tracking/fit_robot_transform.py).
   It tries a plain and a mirrored fit and keeps the better one. Each point's
   error should be well under a foot. Ours came out rotated about 180° and
   mirrored.
3. Paste the six numbers into
   [`homeassistant/packages/roborock_live_position.yaml`](../homeassistant/packages/roborock_live_position.yaml).
   Every 5 seconds while it cleans, Home Assistant writes the robot's
   position in plan feet to `input_number.roborock_x_ft` / `_y_ft`.

Redo this if the robot ever makes a new map.

The inverse (`Minv` in the fit output) goes the other way: tap a spot on your
plan and send the robot there with `roborock.set_vacuum_goto_position`.

## Robot heading + calibration recorder

[`custom_components/roborock_pose`](../custom_components/roborock_pose/) is a
small integration that adds two things on top of the official one:

- **`roborock_pose.get`** returns the robot's x, y **and heading**, which the
  built-in action leaves out. We use it to turn the robot model the right way
  on the 3D dashboard and to drive it by hand from the dashboard.
- **A calibration recorder for room tracking.** Tape your phone flat on top of
  the robot and start a clean. Once a second the Pi records the robot's
  position *and* every scanner's distance reading, on one clock. The robot then
  covers all your open floor for you. Turn a recording into samples with
  [`tracking/robot_rows.py`](../tracking/robot_rows.py) and feed them to the
  radio-map fit ([guide 4](04-room-tracking.md)).
  - `roborock_pose.calib_start` / `calib_stop` / `calib_runs` / `calib_get`.
  - Set `prefix` to your phone's Bermuda sensors, e.g.
    `sensor.my_phone_ble_unfiltered_distance_to_`.
  - **Phone fell off?** Pass `scanners` (each scanner's x, y in feet and
    height in metres) and `xform` (the M and t from above) to `calib_start`,
    and a watchdog compares the readings against where the robot really is. If they stop matching for a few minutes (or no scanner
    hears the phone for 90 s), it pauses the robot and sends you a
    notification. The thresholds are cautious on purpose: the first version
    stopped the robot twice with the phone still on it.

Install: copy the folder to `/config/custom_components/`, add `roborock_pose:`
to `configuration.yaml`, restart.

## Dashboard ideas we built

Tap the robot on the map for a round menu: clean everything, pick rooms, draw a
loop to spot-clean, go to a spot, send it home, or **drive** it with arrows
like a remote-control car. The prompts we used are in
[`prompts/`](../prompts/).

Next: [10. Toothbrush bedtime](10-toothbrush-bedtime.md)
