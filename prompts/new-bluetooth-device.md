# Prompt: make a Bluetooth gadget work in Home Assistant

This is how the Fluval aquarium integration was made. It works for many
"app-only" Bluetooth gadgets.

```text
I have a <device> that is controlled only by its phone app over Bluetooth.
Home Assistant sees its adverts through my ESP32 Bluetooth proxies.

1. Search for prior work: GitHub, the Home Assistant forum, ESPHome
   components. Summarise what is already known about its protocol, and credit
   it.
2. Write a small Python script (bleak) that connects, lists its GATT services
   and characteristics, subscribes to notifications and logs everything.
3. Based on what's known, write the commands for on/off and one setting, and
   test them on the real device one at a time. Tell me the exact bytes sent
   and what changed.
4. When the basics work, wrap it as a Home Assistant custom integration
   (custom_components/<name>) with a config flow that finds the device through
   Home Assistant's bluetooth component (so it works through ESPHome proxies),
   using bleak-retry-connector. Expose it as the right entity types.
5. Document what doesn't work and why.
Keep the phone app closed while testing: most of these devices take one
connection at a time.
```
