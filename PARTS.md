# Parts list

> As an Amazon Associate HouseMaxer earns from qualifying purchases. The links below are affiliate links: they cost you nothing extra and help fund the project.

Prices change daily; check the listing. **Buy used** marks the parts we
think are worth buying used or refurbished (eBay, Amazon Renewed): they
cost the most new and hold up well. Reset anything used to factory
settings before you set it up.

## The brain

Pick one of the three: the Green box, a kit, or the parts one by one. [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) explains the difference.

| Part | Why | Guide |
|---|---|---|
| [Home Assistant Green](https://www.amazon.com/ha_green/dp/B0CXVKSG19?tag=maxestmax-20) | Plug-and-play: Home Assistant already installed. Easiest way in. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [CanaKit Raspberry Pi 5 Starter Kit PRO (8 GB, 128 GB card)](https://www.amazon.com/pi5_kit/dp/B0CRSNCJ6Y?tag=maxestmax-20) | Every Pi part in one box: board, case, fan, power supply, microSD. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [Raspberry Pi 5, 8 GB](https://www.amazon.com/pi5_8gb/dp/B0CK2FCG1K?tag=maxestmax-20) | The board we use. 4 GB is enough for Home Assistant alone. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [Raspberry Pi 27 W USB-C power supply](https://www.amazon.com/pi5_psu/dp/B0D3MFLNC1?tag=maxestmax-20) | The Pi 5 needs 5 V at 5 A; phone chargers make it limit USB power. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [Raspberry Pi Active Cooler](https://www.amazon.com/pi5_cooler/dp/B0CLXZBR5P?tag=maxestmax-20) | Stops the Pi 5 slowing itself down when it gets hot. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [Official Raspberry Pi 5 case with fan](https://www.amazon.com/pi5_case/dp/B0CLY2974P?tag=maxestmax-20) | Case and cooling in one, instead of the Active Cooler. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [SanDisk Extreme 128 GB microSD (A2)](https://www.amazon.com/microsd/dp/B09X7BK27V?tag=maxestmax-20) | Home Assistant writes to disk all day: buy a good card. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |
| [SONOFF Zigbee USB Dongle Plus (ZBDongle-E)](https://www.amazon.com/zigbee_alt/dp/B0B6P22YJC?tag=maxestmax-20) | Zigbee radio for plugs and sensors. We use a Nortek HUSBZB-1, which is no longer sold. | [Guide 1](docs/01-raspberry-pi-and-home-assistant.md) |

## Network

| Part | Why | Guide |
|---|---|---|
| [ASUS ZenWiFi mesh](https://www.amazon.com/s?k=ASUS+ZenWiFi+mesh+WiFi+system&tag=maxestmax-20) · **Buy used** | We use the ZenWiFi AX (XT8) 2-pack, which Amazon no longer stocks new. Any current ZenWiFi works the same with Home Assistant. Good one to buy used. | [Guide 2](docs/02-network-asus-router.md) |

## Bluetooth scanners (one per room)

| Part | Why | Guide |
|---|---|---|
| [ELEGOO ESP32 dev boards, 3-pack (USB-C)](https://www.amazon.com/esp32/dp/B0D8T53CQ5?tag=maxestmax-20) | Bluetooth proxies for Home Assistant and the room tracker. | [Guide 3](docs/03-esp32-bluetooth-scanners.md) |
| [USB-A to USB-C cables, 1 ft, 5-pack](https://www.amazon.com/usbc_cable/dp/B08LH5SX4V?tag=maxestmax-20) | Power and flashing. They carry data, which flashing needs. | [Guide 3](docs/03-esp32-bluetooth-scanners.md) |
| [USB wall chargers, 5-pack (5 V 1 A)](https://www.amazon.com/usb_wall/dp/B0GYMWK6K4?tag=maxestmax-20) | One per board. An ESP32 needs very little power. | [Guide 3](docs/03-esp32-bluetooth-scanners.md) |

## Front door

| Part | Why | Guide |
|---|---|---|
| [August Wi-Fi Smart Lock (4th gen)](https://www.amazon.com/august_lock/dp/B082VXK9CK?tag=maxestmax-20) · **Buy used** | Fits over your deadbolt; your key still works. Comes with DoorSense. We bought ours used on eBay. | [Guide 5](docs/05-front-door-lock.md) |

## Lights

Hue replaced the bulb models we own (LCA005, LCA009, LTA008) in 2025. These are the current versions of the same bulbs.

| Part | Why | Guide |
|---|---|---|
| [Philips Hue Bridge](https://www.amazon.com/hue_bridge/dp/B016H0QZ7I?tag=maxestmax-20) · **Buy used** | Links the bulbs to Home Assistant; works without the internet. Cheap used. | [Guide 6](docs/06-hue-lights.md) |
| [Hue White and Color A19, 1100 lm, 2-pack](https://www.amazon.com/hue_a19_color/dp/B0FNX74DZK?tag=maxestmax-20) | Most of our lamps and ceiling fixtures. | [Guide 6](docs/06-hue-lights.md) |
| [Hue White and Color A21, 1600 lm, 2-pack](https://www.amazon.com/hue_a21/dp/B0FNPK429K?tag=maxestmax-20) | For tall floor lamps that need more light. | [Guide 6](docs/06-hue-lights.md) |
| [Hue White Ambiance A19, 2-pack](https://www.amazon.com/hue_ambiance/dp/B0FMGNGKWR?tag=maxestmax-20) | Warm-to-cool white only, cheaper than color. | [Guide 6](docs/06-hue-lights.md) |

## Curtains

| Part | Why | Guide |
|---|---|---|
| [SwitchBot Curtain 3 (rod)](https://www.amazon.com/switchbot_curtain/dp/B0F8BR5Q66?tag=maxestmax-20) | Clips onto your rod; Bluetooth to Home Assistant. Also sold for U-rail and I-rail: match your track. | [Guide 7](docs/07-switchbot-curtains.md) |
| [SwitchBot Hub 2](https://www.amazon.com/switchbot_hub2/dp/B0BM8VS13P?tag=maxestmax-20) | Optional: puts SwitchBot on Wi-Fi for the app and voice assistants; adds a temperature sensor and IR remote. | [Guide 7](docs/07-switchbot-curtains.md) |

## Aquarium

| Part | Why | Guide |
|---|---|---|
| [Fluval Flex 32.5 gal aquarium kit](https://www.amazon.com/fluval_flex/dp/B07JDTXTGR?tag=maxestmax-20) | Our tank. The integration needs a light that works with the FluvalSmart (Bluetooth) app: check the box before you buy. | [Guide 8](docs/08-fluval-aquarium.md) |
| [SONOFF S40 Lite Zigbee smart plug](https://www.amazon.com/zigbee_plug/dp/B09LV53X62?tag=maxestmax-20) | Switches the tank's UV filter (or anything else) from Home Assistant. | [Guide 8](docs/08-fluval-aquarium.md) |

## Robot vacuum

| Part | Why | Guide |
|---|---|---|
| [Roborock Qrevo Plus (Amazon Renewed)](https://www.amazon.com/roborock_qrevo_plus_renewed/dp/B0FMKBBFLR?tag=maxestmax-20) · **Buy used** | Ours is refurbished. Vacuums, mops, empties itself, washes its pads. | [Guide 9](docs/09-roborock-vacuum.md) |
| [Roborock Qrevo Plus (new / like new)](https://www.amazon.com/roborock_qrevo_plus/dp/B0D2Y8MY5T?tag=maxestmax-20) | Same robot, main listing. | [Guide 9](docs/09-roborock-vacuum.md) |

## Bathroom

| Part | Why | Guide |
|---|---|---|
| [Oral-B iO Series 9](https://www.amazon.com/oralb_io/dp/B0B5HSNPNH?tag=maxestmax-20) | Its Bluetooth state starts the bedtime routine. The iO Series 8 works too. | [Guide 10](docs/10-toothbrush-bedtime.md) |

## Also in our Home Assistant

Not needed for any guide, but they plug into Home Assistant with built-in integrations.

| Part | Why | Guide |
|---|---|---|
| [LG OLED evo C6, 65"](https://www.amazon.com/lg_oled/dp/B0GRK5D3RW?tag=maxestmax-20) | We have the older C2. LG webOS integration: on/off, volume, inputs, and the screen glows on the 3D dashboard. |  |
| [Samsung HW-Q990D soundbar](https://www.amazon.com/q990d/dp/B0CTKV9DRP?tag=maxestmax-20) | Volume and sound modes from Home Assistant. |  |
