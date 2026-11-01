# 6. Lights: Philips Hue

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

We run 15 Hue bulbs on one [Hue Bridge](https://www.amazon.com/hue_bridge/dp/B016H0QZ7I?tag=housemaxer-20):

| Bulb | How many | Where |
|---|---|---|
| [Hue White and Color A19](https://www.amazon.com/hue_a19_color/dp/B0FNX74DZK?tag=housemaxer-20) | 11 | table lamps, ceiling fixtures, shelf lamps |
| [Hue White and Color A21, 1600 lm](https://www.amazon.com/hue_a21/dp/B0FNPK429K?tag=housemaxer-20) | 1 | a tall floor lamp (needs the extra light) |
| [Hue White Ambiance A19](https://www.amazon.com/hue_ambiance/dp/B0FMGNGKWR?tag=housemaxer-20) | 1 | bottom of a paper column lamp |
| Older Hue color A19s | 2 | the same column lamp |

Hue replaced these bulb models in 2025; the links go to the current versions.

**Why Hue:** the bulbs talk Zigbee to their own bridge, so they respond at
once, keep working if the internet is down, and Home Assistant finds the
bridge by itself. Each bulb also works as a normal bulb from the wall switch:
leave the switch on.

**Save money:** Hue bulbs sell in 2- and 4-packs for much less per bulb, and
used Hue bridges are cheap on eBay (reset one with a pin in the hole on the
back before you set it up).

## Set up

1. Set up the bridge and bulbs in the **Hue app**. Make **rooms** there
   (Living Room, Bedroom, Office...). Each Hue room shows up in Home Assistant
   as one light (`light.living_room`) that controls the whole room.
2. Save a scene in each room called **Default**: your normal everyday light.
3. Home Assistant finds the bridge (Settings → Devices & services →
   Discovered → Philips Hue). Press the bridge's button when asked.

## The automations

In [`homeassistant/packages/bedtime.yaml`](../homeassistant/packages/bedtime.yaml):

- **Bedtime fade.** Hallway lights fade out over 12 seconds first (so you can
  walk to bed), then the living room and office, then the curtains close and
  the door locks (only if it's shut). It starts when you brush your teeth
  ([guide 10](10-toothbrush-bedtime.md)).
- **Restore default on turn-on.** After a fade, Hue bulbs come back on at the
  dim level they faded from. So the first time a room turns on after bedtime,
  Home Assistant puts its Default scene back. Only the first time: turn on one
  lamp later in the evening and the rest are left alone. The file has one for
  the living room; copy it for each room.
- **Good morning.** Each room back to its Default scene, and the curtains
  open.
- **Arrival lights** come on when you unlock the door after being away
  ([guide 5](05-front-door-lock.md)).

Next: [7. Curtains](07-switchbot-curtains.md)
