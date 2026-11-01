# 3. ESP32 Bluetooth scanners

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

The cheapest, most useful part of the whole build. Each ESP32 board costs a few
dollars, plugs into a USB wall charger, and becomes a **Bluetooth proxy** for
Home Assistant. Together they:

- stretch Home Assistant's Bluetooth to every room, so the aquarium light, the
  curtains, the toothbrush and the lock all stay in reach;
- hear your phone from several places at once, which is how the house knows
  which room you are in ([guide 4](04-room-tracking.md)).

We run six: five ESP32 boards plus the Pi's own radio. Three is the least that
can place you on a map; one per room works best.

## Parts (per board)

| Part | Link | Notes |
|---|---|---|
| ESP32 dev board | [ESP32-WROOM-32 multipack](https://www.amazon.com/esp32/dp/B0D8T53CQ5?tag=maxestmax-20) | Any "ESP32 DevKit" / `esp32dev` board works. Not the ESP32-S2 (no Bluetooth). |
| USB cable | [USB-A to USB-C cables](https://www.amazon.com/usbc_cable/dp/B08LH5SX4V?tag=maxestmax-20) | Must carry data, not just power, or flashing fails. |
| Wall power | [USB wall chargers, multipack](https://www.amazon.com/usb_wall/dp/B0GYMWK6K4?tag=maxestmax-20) | 5 V, 1 A is plenty. The cheapest ones work. |

## Flash them (once per board, about 3 minutes)

All boards get the **same** firmware:
[`esphome/ble-scanner.yaml`](../esphome/ble-scanner.yaml). Each one names
itself `ble-scanner-` plus the last 6 characters of its own address, so you can
flash a whole bag of them without editing anything.

What the firmware does:
- `bluetooth_proxy` (active): Home Assistant can scan *and* connect through it,
  which the Fluval light and the SwitchBot curtains need.
- An **Identify** button in Home Assistant that blinks the board's blue LED for
  10 seconds, so you can tell which board is which.
- Two quick blinks each time Home Assistant connects: it's alive.
- A Wi-Fi signal sensor.

**Easiest: from Home Assistant.** Install the **ESPHome Device Builder** app
(Settings → Apps), open it, make a new device, paste in `ble-scanner.yaml`,
and fill in its **Secrets** page with the four values from
[`secrets.example.yaml`](../esphome/secrets.example.yaml) (Wi-Fi name,
password, an API key and an update password), then **Install → Plug into this computer** with the board on a USB
cable. (That page needs Chrome or Edge.)

**From your computer:**

```bash
cd esphome
cp secrets.example.yaml secrets.yaml      # fill in Wi-Fi + a new API key
./flash_ble_scanner.sh                     # board plugged in by USB
```

If it hangs at `Connecting...`, hold the **BOOT** button on the board until it
starts writing.

Then, in Home Assistant: **Settings → Devices & services**. The board shows up
under ESPHome as "discovered". Click **Configure** and paste the API key from
your secrets file.

## Where to put them

- **Spread them out**, one per room, near the edges of the home rather than all
  in the middle. The tracker works by comparing distances, so boards close
  together tell it little.
- **Outlet height is fine.** We tested heights from the floor to 8 ft and it
  barely changed accuracy. Being *in the right room* matters far more.
- **Keep them off metal** (behind a fridge, inside a metal shelf) and out of
  cabinets. One of ours sat next to something metal and its readings stopped
  changing as we walked around. Moving it fixed that.
- Write down where each one is on your floor plan (in feet). The tracker needs
  it.

Next: [4. Room tracking](04-room-tracking.md)
