#!/usr/bin/env python3
"""Append (or refresh) an 'Aquarium' section in the HA storage dashboard.

Idempotent: removes any existing section whose heading is 'Aquarium' first,
then appends a fresh one. Makes a timestamped backup before writing.

Before you run it:
  - Install Mushroom from HACS (the editor uses mushroom cards).
  - The dashboard must be a UI-managed (storage) dashboard whose first view is
    a "sections" view. It edits the default dashboard; change PATH for another.
  - Close every open dashboard editor: if the UI saves the dashboard before
    the restart, it overwrites this change.
Run it on the Home Assistant host (for example from the SSH app), then restart
Home Assistant so it reloads the dashboard.
"""

import json
import shutil
import time

PATH = "/config/.storage/lovelace"
# Change these to your own entity IDs (Settings -> Devices -> Fluval BLE Light).
LIGHT = "light.aquarium_light"
MODE = "select.aquarium_light_mode"

section = {
    "type": "grid",
    "cards": [
        {"type": "heading", "heading": "Aquarium", "icon": "mdi:fishbowl"},
        # --- Compact row: always visible ---
        {
            "type": "tile",
            "entity": LIGHT,
            "name": "Aquarium Light",
        },
        {
            "type": "tile",
            "entity": "input_boolean.aquarium_auto",
            "name": "Auto",
            "icon": "mdi:weather-sunset",
            "color": "green",
            "tap_action": {"action": "toggle"},
        },
        {
            "type": "tile",
            "entity": "input_boolean.aquarium_showcase",
            "name": "Show guests",
            "icon": "mdi:eye",
            "color": "amber",
            "tap_action": {"action": "toggle"},
        },
        {
            "type": "tile",
            "entity": "input_boolean.aquarium_edit",
            "name": "Edit",
            "icon": "mdi:pencil",
            "color": "grey",
            "tap_action": {"action": "toggle"},
        },
        # --- Expanding editor: only shown while "Edit" is on ---
        {
            "type": "conditional",
            "conditions": [
                {
                    "condition": "state",
                    "entity": "input_boolean.aquarium_edit",
                    "state": "on",
                }
            ],
            "grid_options": {"columns": "full"},
            "card": {
                "type": "vertical-stack",
                "cards": [
                    {
                        "type": "entities",
                        "title": "Edit schedule",
                        "show_header_toggle": False,
                        "entities": [
                            {"type": "section", "label": "Daytime"},
                            {"entity": "input_datetime.aquarium_sunrise_start", "name": "Sunrise start"},
                            {"entity": "input_datetime.aquarium_sunrise_end", "name": "Full day by"},
                            {"entity": "input_number.aquarium_day_red", "name": "Red"},
                            {"entity": "input_number.aquarium_day_green", "name": "Green"},
                            {"entity": "input_number.aquarium_day_blue", "name": "Blue"},
                            {"entity": "input_number.aquarium_day_white", "name": "White"},
                            {"type": "section", "label": "Nighttime"},
                            {"entity": "input_datetime.aquarium_sunset_start", "name": "Sunset start"},
                            {"entity": "input_datetime.aquarium_sunset_end", "name": "Full night by"},
                            {"entity": "input_number.aquarium_night_red", "name": "Red"},
                            {"entity": "input_number.aquarium_night_green", "name": "Green"},
                            {"entity": "input_number.aquarium_night_blue", "name": "Blue"},
                            {"entity": "input_number.aquarium_night_white", "name": "White"},
                        ],
                    },
                    {
                        "type": "custom:mushroom-template-card",
                        "primary": "Save & close",
                        "secondary": "Changes also apply live as you edit",
                        "icon": "mdi:content-save",
                        "icon_color": "blue",
                        "tap_action": {
                            "action": "perform-action",
                            "perform_action": "script.aquarium_apply_schedule",
                        },
                    },
                ],
            },
        },
    ],
}


def is_aquarium(sec: dict) -> bool:
    cards = sec.get("cards") or []
    for c in cards:
        if c.get("type") == "heading" and c.get("heading") == "Aquarium":
            return True
    return False


def main() -> None:
    shutil.copy(PATH, f"{PATH}.bak.{int(time.time())}")
    with open(PATH) as f:
        data = json.load(f)
    view = data["data"]["config"]["views"][0]
    secs = view.setdefault("sections", [])
    secs[:] = [s for s in secs if not is_aquarium(s)]
    secs.append(section)
    with open(PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK: dashboard now has {len(secs)} sections")


if __name__ == "__main__":
    main()
