# 8. Fish tank: Fluval Flex in Home Assistant

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

Our [Fluval Flex 32.5 gallon](https://www.amazon.com/fluval_flex/dp/B07JDTXTGR?tag=housemaxer-20) has an LED light you control
from the FluvalSmart phone app over Bluetooth. There was no Home Assistant
support for it, so we wrote one:
[`custom_components/fluval_ble`](../custom_components/fluval_ble/).

**Before you buy:** the integration needs a light that pairs with the
**FluvalSmart** app over Bluetooth. Some Flex kits ship with a light run by an
IR remote instead, and the listing doesn't always say which. Check the box or
ask the seller.

It works with Fluval lights that use the FluvalSmart app (Flex, Aquasky,
Plant, Marine, Nano: the ones with the same Bluetooth controller inside). It
runs on Home Assistant's own Bluetooth (the Pi's radio or an ESP32 proxy), so
there is nothing extra to buy.

What you get:
- a **light**: on/off, brightness and colour (red, green, blue, white channels);
- a **mode** picker: manual / automatic / professional (the app's three modes).

The tank's UV filter sits on a cheap [Zigbee smart plug](https://www.amazon.com/zigbee_plug/dp/B09LV53X62?tag=housemaxer-20), so
Home Assistant can switch it too.

## Install

1. Copy `custom_components/fluval_ble/` into your Home Assistant's
   `/config/custom_components/`.
2. Restart Home Assistant.
3. **Close the FluvalSmart app on your phone** (fully, swipe it away). The light
   takes only one Bluetooth connection at a time.
4. Settings → Devices & services → Add integration → **Fluval BLE Light**. Pick
   the device marked ★, choose 4 channels (Flex) or 5 (Plant / Marine), submit.

Channels map in order: 1 red, 2 green, 3 blue, 4 white. If yours come out
swapped, reorder them where `light.py` builds the colour.

## The schedule (and why Home Assistant runs it)

The light has its own sunrise/sunset schedule, but **its controller refuses to
accept a new schedule from anything but the Fluval app**. Its Bluetooth chip
only takes tiny 20-byte packets, and the schedule needs several in a row. So
instead Home Assistant runs the schedule itself:
[`homeassistant/packages/aquarium.yaml`](../homeassistant/packages/aquarium.yaml).

- You set sunrise start/end, sunset start/end, a daytime colour and a night
  colour from the dashboard.
- Every 5 minutes (and whenever you change a setting) a script works out the
  colour for right now, fading smoothly through sunrise and sunset, and sets
  the light in manual mode.
- **Show guests**: one tap for full bright white; tap again to go back to the
  schedule.

The trade-off: the schedule only moves while Home Assistant is running and in
Bluetooth range of the tank. If the Pi is off, the light stays on its last
colour.

Change `light.aquarium_light` in the package to your light's entity ID. Then
put the helpers on a dashboard: the four times, the eight colour sliders, and
the Auto and Show guests switches. The dashboard editor is the simplest way.
Ours (tiles, plus a colour editor that only shows when you tap Edit) was
written by [`tools/build_aquarium_dashboard.py`](../tools/build_aquarium_dashboard.py);
read the notes at its top first, as it edits the dashboard file directly.

## How it works

Each command is a short frame (`0x68`, a command byte, its arguments, and an
XOR checksum), scrambled with Fluval's simple XOR scheme and written to the
light over Bluetooth. Status comes back as notifications split across several
packets. Home Assistant users worked out the protocol, mainly mrzottel with
an ESPHome `fluval_ble_led` component, in the
[Fluval Aquasky BLE thread](https://community.home-assistant.io/t/fluval-aquasky-ble-rgb-light/259598).
We rewrote it in Python as a Home Assistant integration and checked the on/off
bytes against real captures.

## Known limits

- One connection at a time: while Home Assistant is connected, the phone app
  can't connect, and the other way round. To change something in the app,
  disable the integration first (⋮ → Disable), then turn it back on.
- `fluval_ble.set_auto_schedule` exists but the light ignores it (see above).

Next: [9. Robot vacuum](09-roborock-vacuum.md)
