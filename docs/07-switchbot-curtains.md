# 7. Curtains: SwitchBot

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

Two [SwitchBot Curtain](https://www.amazon.com/switchbot_curtain/dp/B0F8BR5Q66?tag=maxestmax-20) motors pull our bedroom
curtains open and shut. They clip onto the rod you already have, run on a
battery (charge every few months, or add the solar panel), and come off when
you move out. Buy the version that matches your rod: **rod**, **U-rail** or
**I-rail**.

The [SwitchBot Hub 2](https://www.amazon.com/switchbot_hub2/dp/B0BM8VS13P?tag=maxestmax-20) is optional with Home Assistant, but
we use it: it puts the curtains on Wi-Fi for the SwitchBot app and voice
assistants, and it has a temperature and humidity sensor and an IR blaster.

## Set up

1. Set each motor up in the **SwitchBot app** and run its calibration (it
   learns where open and closed are). If you have two motors on one window,
   pair them as a group in the app so they meet in the middle.
2. Home Assistant's built-in **SwitchBot Bluetooth** integration finds each
   motor through your ESP32 proxies. It talks to them over Bluetooth directly,
   with no cloud. You get `cover.curtain_left` / `cover.curtain_right` with
   open, close and position.
3. Bluetooth range is short. If a motor shows "unavailable", put an ESP32
   board in that room ([guide 3](03-esp32-bluetooth-scanners.md)).

## Automations

In [`homeassistant/packages/bedtime.yaml`](../homeassistant/packages/bedtime.yaml):
curtains close at bedtime, open with "Good morning", and open when you leave
(daylight for the plants and fish while you're out).

Next: [8. Fish tank](08-fluval-aquarium.md)
