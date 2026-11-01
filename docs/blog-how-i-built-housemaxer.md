# How I turned a rented apartment into a smart home for the price of a robot vacuum

*The HouseMaxer write-up. The step-by-step guides and code are in this repo; this
is the story of how it came together and what I'd tell a friend.*

I rent. I can't rewire anything, I can't drill much, and whatever I install
has to come off when I move. I also didn't want a pile of apps, a monthly fee
for each gadget, or a home that stops working when some company's server goes
down. What I wanted was simple to say: the home should notice what I'm doing
and help, without me asking.

Here's where it ended up.

- I walk up to my door with my hands full, and it unlocks. I walk out, and it
  locks behind me.
- At night I brush my teeth, and the hallway lights fade, then the rest of the
  apartment, then the curtains close and the door locks. In the morning the
  lights come back to normal, not the dim level they faded from.
- The fish tank has a sunrise and a sunset. When friends come over, one tap
  makes it bright.
- The robot vacuum shows up on a live map of my apartment. So do I.

## The brain: one Raspberry Pi

Everything runs on a Raspberry Pi 5 with Home Assistant, the free, open-source
hub that talks to almost anything. It sits by my router, on Ethernet, and never
needs the cloud for the things that matter.

I set mine up as a normal Linux box that *also* runs Home Assistant, so the Pi
could do other jobs too. That method has since lost official support, so the
guide explains both what I did and what I'd do today. If you just want it to
work, buy the Home Assistant Green and skip the terminal entirely.
([Guide 1](01-raspberry-pi-and-home-assistant.md))

## The best $5 I spent: Bluetooth boards

The most useful thing in my apartment costs a few dollars a board. ESP32
boards are tiny Wi-Fi + Bluetooth computers. Flashed with one shared firmware
and plugged into USB chargers around the apartment, they become Bluetooth
listeners for Home Assistant in every room.

That fixed two problems at once. Bluetooth gadgets that used to drop off (the
fish tank light, the curtain motors, the toothbrush) now always reach Home
Assistant. And with several of them hearing my phone, the house can tell which
room I'm in. ([Guide 3](03-esp32-bluetooth-scanners.md))

## Knowing where I am

My first try at room tracking was the textbook one: each board estimates how
far away my phone is, and you find where the circles cross. In a real home the
dot jumped around and often sat in the wrong room. Walls, furniture and my own
body all weaken the signal, and every cheap board hears a bit differently.

So I stopped trusting the physics and measured instead. I walked around the
apartment tapping where I was on a map while the boards logged what they
heard. From that, the computer learned each board's quirks: how its readings
grow with distance, how much each wall costs, and which way it hears best.
The tracker also knows where the walls and doors are, so the dot can't jump
through a wall. It walks through the doorway like I do.

It's not perfect: half the time it is within about 5 ft, and it picks the
right room about three times in four. The fit also tells me when a board is
wrong. One board's readings barely changed as I walked
around; it turned out to be next to something metal. Another was simply
pinned in the wrong spot on my map.

Then I had a better idea for gathering data: tape the phone to the robot
vacuum. It drives over every bit of open floor, knows exactly where it is, and
doesn't get bored. The Pi records the robot's position and every Bluetooth
reading on one clock, and a watchdog pauses the robot if the phone falls off.
([Guide 4](04-room-tracking.md), [Guide 9](09-roborock-vacuum.md))

## The door that opens for me (and only me)

Walk-up unlock is the feature everyone asks about and the one you must get
right, because a mistake opens your front door.

The trick is an "away latch": a switch that only turns on when the house has
*really* lost my phone, and that clears the moment the door unlocks. The door
can open itself once when I come home, and never again until I leave again.

I found out why "really" matters when it went wrong. During a FaceTime call my
phone briefly vanished from Bluetooth while I was sitting 18 feet from the
door. The house decided I'd left, armed the latch, and unlocked the door. Now
it needs two signals that agree (off the Wi-Fi *and* gone from Bluetooth)
before it believes I'm gone. The lock automations in the repo carry notes like
that one: what went wrong, and the fix. ([Guide 5](05-front-door-lock.md))

I bought the lock used on eBay, and the robot vacuum refurbished. For the
expensive parts, buy used, reset them, and they work like new.

## The fish tank nobody supported

My Fluval Flex aquarium light only works with Fluval's own phone app, and
nobody had built Home Assistant support for it. The community had worked out
most of its Bluetooth language, so I built an integration on top of that:
on/off, brightness, colour and mode.

One thing wouldn't work: the light refuses new schedules from anything but
its own app. So Home Assistant runs the schedule instead, re-computing the
colour every five minutes and fading smoothly through sunrise and sunset. You
set it all from the dashboard. ([Guide 8](08-fluval-aquarium.md))

## A home you can look at

The last piece was the dashboard. I scanned the
apartment with my phone's LiDAR, had an AI write a script that rebuilt it
cleanly in Blender, tagged every smart device with its Home Assistant name,
and put the result in a 3D card on the dashboard. Lamps glow when they're on,
curtains slide, the door swings open, the robot drives around, and tapping
anything opens a little round menu of what it can do.
([Guide 11](11-dashboards-and-3d.md))

I don't publish my own model or floor plan: that's a map of where I live. But
the prompts I used are in the repo, so you can make yours.

## Building it with an AI

I built most of this by working with Claude in a terminal, one feature per
conversation. What made it work: give it a Home Assistant token so it can look
for itself, make it back up everything before changing it, and make it prove
results with a screenshot or a number instead of "should work now". The
prompts are in [`prompts/`](../prompts/).

## What it cost

Home Assistant is free. The Pi with power, cooling and card costs about the
same as one smart lock, ESP32 boards are a few dollars each, and the rest
is the gadgets you'd buy anyway (lights, a lock, a vacuum). Buy those used
where you can. The full list is in [PARTS.md](../PARTS.md).

*As an Amazon Associate HouseMaxer earns from qualifying purchases.*
