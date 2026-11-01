# Prompt: first contact with your Home Assistant

Use this once Home Assistant is running and you have made a long-lived access
token (Profile → Security). Save the token in a file only you can read, e.g.
`~/.ha_token` with `chmod 600`.

```text
My Home Assistant is at http://homeassistant.local:8123. A long-lived access
token is in ~/.ha_token (read it from the file; never print it or write it
anywhere else).

1. Using the WebSocket API, list every integration, device (maker + model) and
   entity, grouped by room/area. Save it as inventory.md.
2. Flag anything unavailable, any device not in an area, and any integration
   that failed to load, with the likely fix.
3. Suggest 10 automations that fit what I own. For each: what triggers it, what
   it does, which entities it uses, and anything that could go wrong (for
   locks: how it could unlock by mistake).
Don't change anything yet.
```

Follow-ups that worked well:

```text
Build automation #3 as a Home Assistant package file. Back up anything you
change first. After you deploy it, trigger it once and show me the trace.
```

```text
The automation fired when it shouldn't have at 9:22 PM yesterday. Pull the
history of every entity it uses from 9:00 to 9:30, tell me exactly why it
fired, and propose the smallest change that stops it without breaking the
normal case.
```
