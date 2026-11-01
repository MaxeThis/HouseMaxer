# 2. The network: ASUS ZenWiFi mesh

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

Every device in this build uses the Wi-Fi, so it has to reach every
corner. We use an ASUS ZenWiFi AX (XT8) two-pack: two mesh units, one by the
modem and one at the far end of the home, so the ESP32 boards and the robot
vacuum never drop off. The XT8 is no longer sold new; buy one used, or any
[current ASUS ZenWiFi](https://www.amazon.com/s?k=ASUS+ZenWiFi+mesh+WiFi+system&tag=maxestmax-20). All of them have the features below.

## What the router does for Home Assistant

1. **Presence.** The built-in **ASUSWRT** integration (Settings → Devices &
   services → Add → ASUSWRT) tells Home Assistant which phones are on the home
   Wi-Fi. That gives you `device_tracker.<phone>` = `home` / `not_home`. It is
   one of the two signals the door lock trusts
   ([guide 5](05-front-door-lock.md)). On the iPhone, tap the (i) next to your
   home network and set **Private Wi-Fi Address** to **Fixed** (or Off), or the
   router sees a new random device every so often.
2. **Fixed addresses.** LAN → DHCP Server → Manually Assigned IP: give the
   Raspberry Pi, the Hue Bridge and the soundbar fixed addresses.
3. **A guest network for devices you don't trust.** Cheap cloud gadgets go on
   a guest network. But a guest network normally can't see the rest of your
   network, and Home Assistant then can't talk to them. ASUS has a switch for
   this: Guest Network → edit → **Access Intranet → Enable**. Our Roborock
   lives on the 2.4 GHz guest network with Access Intranet on, and Home
   Assistant reaches it locally.

## Tips

- Most smart devices (ESP32 boards, plugs, the robot) only speak 2.4 GHz. If
  setup fails, make sure 2.4 GHz is on and has its own name, or turn off
  "Smart Connect" while you add the device.
- Put the Raspberry Pi on Ethernet, not Wi-Fi.
- The **UPnP** integration that Home Assistant finds on its own gives you
  sensors for how much data is moving and whether the internet link is up,
  handy for an "is the internet down?" card.

Next: [3. ESP32 Bluetooth scanners](03-esp32-bluetooth-scanners.md)
