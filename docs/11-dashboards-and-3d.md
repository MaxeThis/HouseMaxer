# 11. Dashboards: a live map and a 3D home

The last piece is the dashboard. Ours has two views of the home, both live:

- **The map (2D):** a top-down floor plan. A dot follows you from room to room
  ([guide 4](04-room-tracking.md)), the robot vacuum glides across it, and every
  device sits where it really is: tap a lamp to turn it on, tap the lock to
  lock it, tap the robot for its menu.
- **The 3D home:** a dollhouse model of the home you can spin with a finger.
  Lamps glow and light their room, curtains slide, the front door swings open
  when DoorSense says so, a ring around the lock turns red or green, the TV
  screen lights up, the robot drives around, and walls between you and what
  you're looking at fade out. Tap anything for a round menu of what it can do.

We don't publish our own cards: they hold our floor plan and our model. Below
is how we made them, so you can make yours, and
[`prompts/`](../prompts/) has the prompts we gave Claude at each step.

## How the 3D home was made

1. **Scan the rooms with a phone.** We used Scaniverse, a free LiDAR scanning
   app, on an iPhone Pro (any app that exports `.usdz` or `.obj` works) and
   walked each room slowly.
2. **Rebuild it clean in Blender.** A raw scan is lumpy and huge. We had Claude
   write a Python script for Blender that builds clean walls, doors, windows
   and furniture from a JSON "spec" (room sizes, where each thing sits),
   measuring off the scan. Edit the JSON, rerun the script, get a new model.
   That is far easier than hand-modelling.
3. **Tag every smart device** in the model with its Home Assistant entity ID
   (a custom property on the object), and use the *same* coordinates as the 2D
   map (feet from the top-left corner), so the tracker, the robot and the model
   all agree on where things are.
4. **Export a `.glb`** (compressed with Draco) and put it in `/config/www/`.
5. **Write a custom Lovelace card** with [three.js](https://threejs.org/) that
   loads the `.glb`, finds the tagged objects, and changes them as Home
   Assistant states change. Bundle it with esbuild into one `.js` file, add it
   under Settings → Dashboards → ⋮ → Resources (turn on Advanced mode in your
   user profile if you don't see it), and put the card on a dashboard.

Tips from our mistakes:
- Give each device its own copy of its material, or turning on one lamp makes
  everything that shares that material glow.
- Only things that are really lit should glow. Use a faint outline to show
  what you can tap.
- Keep the 2D map and 3D model in one shared coordinate system from day one.
- Keep a backup of the card file before every change; we went through 20
  versions in two days.

## Make it yours, not ours

Use your own floor plan, your own model and your own icons. Don't copy
characters, logos or art from games or brands into your dashboard; describe
the *feel* you want ("dollhouse view, round pop-up menus, soft glow on hover")
and let your AI helper draw it from scratch. Everything in this repo is our
own work or is credited.

Next: back to the [README](../README.md) or the [parts list](../PARTS.md).
