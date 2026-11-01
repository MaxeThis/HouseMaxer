# 1. The brain: Raspberry Pi + Home Assistant

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

Everything in HouseMaxer runs on one Raspberry Pi 5 with
[Home Assistant](https://www.home-assistant.io/). The Pi sits next to the
router, plugged in by Ethernet, and talks to every device in the house: over
Wi-Fi, over Bluetooth (its own radio plus the ESP32 boards), and over Zigbee and
Z-Wave (a USB stick).

## Pick your hardware: three ways in

| | What you buy | Time to set up | Can it run other things? | About |
|---|---|---|---|---|
| **1. Plug and play** | [Home Assistant Green](https://www.amazon.com/ha_green/dp/B0CXVKSG19?tag=maxestmax-20) | 10 minutes | No. Home Assistant only (plus its apps). | $$ |
| **2. Kit** | [Raspberry Pi 5 starter kit](https://www.amazon.com/pi5_kit/dp/B0CRSNCJ6Y?tag=maxestmax-20) (board, case, fan, power supply, microSD) | An evening | Yes | $$$ |
| **3. Piece by piece** | Pi 5 board, power supply, cooler or case, microSD (list below) | An evening | Yes | $$–$$$ |

**Pick 1** if you only want Home Assistant and never want to open a terminal.
The Green is the box Home Assistant itself sells. It is slower than a Pi 5 and
has no Bluetooth of its own, which matters less once you add ESP32 Bluetooth
proxies ([guide 3](03-esp32-bluetooth-scanners.md)).

**Pick 2** if you want the Pi but not the shopping. A kit has every part in one
box and you know they fit together.

**Pick 3** if you already own some of the parts (a USB-C charger, a microSD
card) or want to choose each one. This is what we did. You need all four of:

| Part | What we use | Why |
|---|---|---|
| Board | [Raspberry Pi 5, 8 GB](https://www.amazon.com/pi5_8gb/dp/B0CK2FCG1K?tag=maxestmax-20) | 4 GB runs Home Assistant fine. 8 GB leaves room for other programs beside it. |
| Power | [Official 27 W USB-C power supply](https://www.amazon.com/pi5_psu/dp/B0D3MFLNC1?tag=maxestmax-20) | The Pi 5 wants 5 V at 5 A. Phone chargers make it throttle its USB ports, and the Zigbee stick lives on one. |
| Cooling | [Official Active Cooler](https://www.amazon.com/pi5_cooler/dp/B0CLXZBR5P?tag=maxestmax-20) or [official case with fan](https://www.amazon.com/pi5_case/dp/B0CLY2974P?tag=maxestmax-20) | A Pi 5 without cooling slows itself down under load. |
| Storage | [128 GB A2 microSD](https://www.amazon.com/microsd/dp/B09X7BK27V?tag=maxestmax-20) | Home Assistant writes to disk all day. Buy a known brand with an A2 rating. Ours has 115 GB and uses 15. |

You also need a microSD card reader for your computer (most kits include one)
and an Ethernet cable.

### The radio stick (Zigbee + Z-Wave)

Zigbee plugs and sensors need a USB radio. We use a Nortek HUSBZB-1, which
does Zigbee and Z-Wave in one stick, but it is no longer sold. For Zigbee get a
[SONOFF ZBDongle-E](https://www.amazon.com/zigbee_alt/dp/B0B6P22YJC?tag=maxestmax-20) (or Home Assistant's own Connect ZBT-2 from
their site); add a separate Z-Wave stick only if you own Z-Wave devices. Plug the stick into a short USB extension
cable, not straight into the Pi: the Pi's own USB 3 ports put out noise that
drowns Zigbee.

## Installing Home Assistant: two ways

### The normal way: Home Assistant OS (do this one)

Home Assistant OS turns the Pi into an appliance. Updates, backups and apps
all work from the web page.
(Home Assistant renamed add-ons to **Apps** in 2026.2; older guides say
add-ons.)

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your computer.
2. Choose **Raspberry Pi 5**, then **Other specific-purpose OS → Home assistants
   and home automation → Home Assistant**, then your microSD card. Write it.
3. Put the card in the Pi, plug in Ethernet, then power.
4. After a few minutes open `http://homeassistant.local:8123` and follow the
   setup screens.

"But I want to run other things on the Pi too": most of those exist as
apps. Ours runs these, all from **Settings → Apps**: Advanced SSH & Web
Terminal, Tailscale (remote access without opening ports), ESPHome Device
Builder, Matter Server and Z-Wave JS.

### What we did: Home Assistant Supervised on Raspberry Pi OS

We wanted the Pi to stay a normal Linux computer that *also* runs Home
Assistant with its apps, backups and one-click updates. We could run
anything we liked beside it (a print server for the printer, our own scripts,
plain Docker containers) and still have the full Home Assistant.

> **Read this first.** Home Assistant stopped supporting the Supervised method
> with release 2025.12
> ([their announcement](https://www.home-assistant.io/blog/2025/05/22/deprecating-core-and-supervised-installation-methods-and-32-bit-systems/)).
> And Raspberry Pi OS was never on the supported list even before that; only
> plain Debian was. Ours still runs and still updates (2026.10 at the time of
> writing), but **Settings → System → Repairs** marks it "unsupported", Home
> Assistant will not help if it breaks, and the installer may stop working
> one day. If you want the same freedom on a supported setup, run Home
> Assistant OS and use apps, or run
> [Home Assistant Container](https://www.home-assistant.io/installation/linux#docker-compose)
> on Raspberry Pi OS (you lose apps, but Docker can run the same programs).

Here is what we ran, for the record. It assumes you are comfortable in a
terminal.

1. **Flash Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager. In the
   settings gear set a hostname (say `homepi`, so it answers at
   `homepi.local`), a user, and your SSH key. Boot it on Ethernet and SSH in.

2. **Update and install what the Supervisor needs:**

   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo apt install -y apparmor cifs-utils curl dbus jq libglib2.0-bin lsb-release \
     network-manager nfs-common systemd-journal-remote systemd-resolved udisks2 wget
   ```

   Raspberry Pi OS (Bookworm) already uses NetworkManager, so you can skip the
   "switch from ifupdown" step the official installer lists.

3. **Turn on AppArmor.** Add `apparmor=1 security=apparmor` to the end of the
   single line in `/boot/firmware/cmdline.txt` (same line, a space before it),
   then `sudo reboot`. Check with `sudo aa-status`.

4. **Install Docker:**

   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   ```

5. **Install OS Agent** (it lets the Supervisor control the Pi). Get
   the `linux_aarch64.deb` from the
   [os-agent releases](https://github.com/home-assistant/os-agent/releases)
   (we run 1.6.0) and install it:

   ```bash
   wget https://github.com/home-assistant/os-agent/releases/download/1.6.0/os-agent_1.6.0_linux_aarch64.deb
   sudo dpkg -i os-agent_1.6.0_linux_aarch64.deb
   ```

6. **Install the Supervised package:**

   ```bash
   curl -L -o homeassistant-supervised.deb \
     https://github.com/home-assistant/supervised-installer/releases/latest/download/homeassistant-supervised.deb
   sudo apt install ./homeassistant-supervised.deb
   ```

   When it asks for the machine type, pick **raspberrypi5-64**.

7. Wait 5–10 minutes while it pulls its containers, then open
   `http://<hostname>.local:8123`.

What you get: Home Assistant and the Supervisor run in Docker, and the rest of
the Pi is yours. Don't run `apt` upgrades that replace Docker with a different
version, and don't stop containers whose names start with `hassio_` or
`addon_`: the Supervisor manages those.

## After either install

- **Make a backup plan on day one.** Settings → System → Backups → set up
  automatic backups, and store a copy off the Pi (Home Assistant Cloud, a
  network share, or Google Drive through an app). A microSD card can die.
- **Install HACS** (the community store). We use it for
  [Bermuda](https://github.com/agittins/bermuda), the Bluetooth room tracker.
  Follow [hacs.xyz](https://hacs.xyz/docs/use/).
- **Turn on packages** so you can drop the YAML files from this repo straight
  in. Add this to `/config/configuration.yaml` and restart:

  ```yaml
  homeassistant:
    packages: !include_dir_named packages
  ```

  Then copy files from [`homeassistant/packages/`](../homeassistant/packages/)
  into `/config/packages/`, one at a time, after you have set up the devices
  that file uses. Each file lists at the top which entity IDs to change.
- **Give it a fixed address** on your router (a DHCP reservation), so phones
  and ESP32 boards always find it. See [guide 2](02-network-asus-router.md).

Next: [2. The network](02-network-asus-router.md)
