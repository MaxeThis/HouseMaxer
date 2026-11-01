# 10. Bedtime starts with your toothbrush

> *Product links on this page are Amazon affiliate links. As an Amazon Associate HouseMaxer earns from qualifying purchases.*

Our favourite automation, and the cheapest if you already own the brush. The
[Oral-B iO Series 9](https://www.amazon.com/oralb_io/dp/B0B5HSNPNH?tag=maxestmax-20) sends out its state over Bluetooth, and
Home Assistant hears it through the ESP32 proxies.

**Brush your teeth after 9 PM and the house gets ready for bed:**

1. hallway lights fade out over 12 seconds, so you can still walk to bed;
2. then the living room and office lights fade;
3. the curtains close;
4. the front door locks.

No button, no voice command, no app. You were going to brush anyway.

## Set up

1. Home Assistant finds the brush by itself (the built-in **Oral-B**
   integration) the first time you turn it on near a Bluetooth proxy. Add it.
2. You get a set of sensors. The one that matters reads `running` while the
   brush is on. Check its name in Developer tools → States.
3. Copy [`homeassistant/packages/bedtime.yaml`](../homeassistant/packages/bedtime.yaml)
   into `/config/packages/`, change the entity IDs to yours, restart.

The time window is 9 PM to 4 AM, so morning brushing does nothing. Most
Oral-B iO and Genius models with Bluetooth should work; the brush has to be in
range of a scanner in the bathroom.

Next: [11. Dashboards and the 3D home](11-dashboards-and-3d.md)
