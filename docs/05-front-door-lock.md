# 5. Front door lock: unlock as you walk up

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

We use an [August Wi-Fi Smart Lock (4th gen)](https://www.amazon.com/august_lock/dp/B082VXK9CK?tag=maxestmax-20) (August is part
of Yale now). It fits over the inside half of your existing deadbolt, so the
key outside still works and a renter can put the old one back when they move
out. It comes with **DoorSense**, a small magnet that tells it whether the door
is shut.

> **We bought ours used on eBay**, and we suggest that for the pricier parts
> of this build. Smart locks, robot vacuums and mesh routers sell used for far
> less than new. For a lock: make sure the seller includes the DoorSense
> magnet and mounting plate, then **factory-reset it and set it up as new** in
> the August app, so no one else's account can open your door.

## Hook it up to Home Assistant

1. Set the lock up in the **August** app first (calibrate DoorSense there).
2. In Home Assistant add the **August** integration and sign in with the same
   account on the August page that opens. No paid plan is needed. You get
   `lock.front_door` and `binary_sensor.front_door_door` (open / closed).
3. Optional: the **Yale Access Bluetooth** integration can talk to the lock
   directly over Bluetooth through your ESP32 proxies, so it keeps working if
   the internet is down. It needs the lock's offline key, which the August
   integration fetches for you.

## The automations

All of these are in
[`homeassistant/packages/presence_lock.yaml`](../homeassistant/packages/presence_lock.yaml),
which also needs [`bedtime.yaml`](../homeassistant/packages/bedtime.yaml)
(it defines the "Away" script).

**Lock on leave.** Phone leaves the home Wi-Fi and DoorSense says the door is
shut → lock.

**Walk-up unlock.** This is the one people ask about, and the one you must get
right, because a wrong guess opens your front door. It uses an **away latch**:
a switch (`input_boolean.away_latch`) that means "the house has really lost
you".

1. **Arm the latch** only when the house has truly lost the phone: it is off
   the home Wi-Fi **and** Bluetooth either can't hear it or reads it further
   than 40 ft away. One signal is never enough. Once, during a FaceTime call,
   our Bluetooth tracker said "away" while the phone was 18 ft from the door;
   the latch armed and the door unlocked by itself. And phones drop off Wi-Fi
   for a moment while asleep. Needing both rules out each mistake.
2. **Unlock** when the latch is armed and the phone reads closer than 25 ft to
   a scanner for 3 seconds. Where we park reads well over 40 ft, so it cannot
   fire from the car.
3. **Any unlock clears the latch**, so it fires once per trip. No timers.
4. **Auto-reset:** if the latch is on but the phone has been home on Wi-Fi
   *and* Bluetooth for 10 minutes, clear it.
5. The unlock is brief: unlock, wait a minute, then lock again once DoorSense
   says the door is shut (it never throws the bolt into an open door). If the
   door is still open after 10 minutes you get a notification, and it still
   locks the moment the door shuts.

**How safe is a Bluetooth unlock?** Your phone's Bluetooth address changes
every few minutes and only your IRK can recognise it, so a stranger can't just
pretend to be your phone. Someone could, in theory, record your phone's signal
and replay it by your door within those few minutes, but only while the latch
is armed and only once. Turn on the August app's own auto-lock as a backstop.

**Tune the numbers for your home.** Watch `sensor.<phone>_ble_distance` in
Developer tools while you stand outside your door, then where you park. Pick an
"at the door" number a little above the first reading, and a "gone" number
between the two. (Bermuda reports metres if your Home Assistant is metric.)

**Arrival lights.** The door unlocks while you were away (or got back in the
last minute) → entry and living room lights on.

**Auto-reset for the cloud link.** The August connection sometimes drops after a
router or Home Assistant restart. If the lock is unavailable for 5 minutes,
Home Assistant reloads the integration, and keeps trying every 15 minutes, and
leaves you a notification if it can't.

## Safety notes

- Test every change with the latch *off* first, by watching the automation
  traces (Settings → Automations → ⋮ → Traces).
- Keep a key. Locks run on batteries.
- Don't share your Home Assistant with anyone you would not give a key to.

Next: [6. Hue lights](06-hue-lights.md)
