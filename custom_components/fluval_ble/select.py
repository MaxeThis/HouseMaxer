"""Select platform exposing the Fluval lighting mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODES, MODES_REVERSE
from .fluval import FluvalDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fluval mode select."""
    device: FluvalDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FluvalModeSelect(entry, device)])


class FluvalModeSelect(SelectEntity):
    """Manual / automatic / professional mode selector."""

    _attr_has_entity_name = True
    _attr_name = "Mode"
    _attr_icon = "mdi:tune-variant"
    _attr_options = list(MODES.values())

    def __init__(self, entry: ConfigEntry, device: FluvalDevice) -> None:
        self._device = device
        address = entry.data["address"]
        self._attr_unique_id = f"{address}_mode"
        self._attr_device_info = DeviceInfo(
            connections={("bluetooth", address)},
            identifiers={(DOMAIN, address)},
            name=entry.title,
            manufacturer="Fluval",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._device.add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._device.status.available

    @property
    def current_option(self) -> str | None:
        return MODES.get(self._device.status.mode)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Expose the device's stored automatic schedule, if known."""
        a = self._device.status.auto
        if not a:
            return None

        def _hm(m: int) -> str:
            m = int(m)
            return f"{m // 60:02d}:{m % 60:02d}"

        return {
            "auto_sunrise_start": _hm(a["sunrise_start"]),
            "auto_sunrise_end": _hm(a["sunrise_end"]),
            "auto_sunset_start": _hm(a["sunset_start"]),
            "auto_sunset_end": _hm(a["sunset_end"]),
            "auto_day_levels": a["day"],
            "auto_night_levels": a["night"],
        }

    async def async_select_option(self, option: str) -> None:
        mode = MODES_REVERSE.get(option)
        if mode is not None:
            await self._device.async_set_mode(mode)
