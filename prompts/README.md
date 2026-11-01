# Prompts

We built most of HouseMaxer by working with Claude (Claude Code, in a terminal
on a Mac on the same network as the Pi). These are the prompts that worked, in
the order we used them, cleaned up so they fit any home.

How we work with an AI helper:

1. **Give it access.** A Home Assistant long-lived access token in a file it can
   read (never paste tokens into a public place), and the address of your Home
   Assistant. With that it can read your devices and states itself instead of
   asking you.
2. **One feature per conversation.** "Add the robot to the map" is a good size.
   "Build my smart home" is not.
3. **Make it back up first.** Every prompt below asks for a backup of whatever
   it changes. Dashboards and cards are easy to break.
4. **Make it prove things.** Ask for a screenshot, a trace, or a number
   ("median error in feet"), not "it should work now".

| File | What it builds |
|---|---|
| [setup-and-inventory.md](setup-and-inventory.md) | First contact: list every device, suggest automations |
| [room-tracker-card.md](room-tracker-card.md) | The 2D map card with the live dot, device pins and calibration |
| [3d-home-card.md](3d-home-card.md) | Scan → Blender model → 3D dashboard card |
| [roborock-on-the-map.md](roborock-on-the-map.md) | Robot vacuum on your floor plan, tap-to-go, remote driving |
| [new-bluetooth-device.md](new-bluetooth-device.md) | Reverse-engineering a Bluetooth gadget into an integration (how the Fluval one was made) |
