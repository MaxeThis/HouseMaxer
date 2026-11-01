"""Light platform for Fluval BLE Light."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CHANNEL_MAX, DOMAIN, MODE_MANUAL
from .fluval import FluvalDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fluval light entity."""
    device: FluvalDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FluvalLight(entry, device)])


def _to_ha(value: int) -> int:
    """Channel level (0..1000) -> 0..255."""
    return round(value / CHANNEL_MAX * 255)


def _to_fluval(value: int) -> int:
    """0..255 -> channel level (0..1000)."""
    return round(value / 255 * CHANNEL_MAX)


class FluvalLight(LightEntity):
    """A Fluval aquarium light exposed as an RGBW/RGBWW light."""

    _attr_has_entity_name = True
    _attr_name = None  # use the device name

    def __init__(self, entry: ConfigEntry, device: FluvalDevice) -> None:
        self._entry = entry
        self._device = device
        self._address = entry.data["address"]
        self._num = device.num_channels

        if self._num == 5:
            self._attr_color_mode = ColorMode.RGBWW
            self._attr_supported_color_modes = {ColorMode.RGBWW}
        else:
            self._attr_color_mode = ColorMode.RGBW
            self._attr_supported_color_modes = {ColorMode.RGBW}

        self._attr_unique_id = f"{self._address}_light"
        self._attr_device_info = DeviceInfo(
            connections={("bluetooth", self._address)},
            identifiers={(DOMAIN, self._address)},
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
    def is_on(self) -> bool:
        return self._device.status.on

    @property
    def brightness(self) -> int | None:
        chans = self._device.status.channels[: self._num]
        if not chans:
            return None
        return _to_ha(max(chans))

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        if self._num != 4:
            return None
        return self._scaled_color(4)  # type: ignore[return-value]

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        if self._num != 5:
            return None
        return self._scaled_color(5)  # type: ignore[return-value]

    def _scaled_color(self, n: int) -> tuple[int, ...] | None:
        """Normalize channels to a full-brightness color tuple (0..255)."""
        chans = self._device.status.channels[:n]
        peak = max(chans) if chans else 0
        if peak == 0:
            return tuple([0] * n)
        return tuple(round(c / peak * 255) for c in chans)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on, optionally setting brightness/color (manual mode)."""
        color_changed = (
            ATTR_RGBW_COLOR in kwargs
            or ATTR_RGBWW_COLOR in kwargs
            or ATTR_BRIGHTNESS in kwargs
        )

        if not color_changed:
            await self._device.async_set_power(True)
            return

        # Color/brightness control only works in manual mode.
        if self._device.status.mode != MODE_MANUAL:
            await self._device.async_set_mode(MODE_MANUAL)

        # Determine the target normalized color (0..255 per channel).
        if ATTR_RGBW_COLOR in kwargs:
            color = list(kwargs[ATTR_RGBW_COLOR])
        elif ATTR_RGBWW_COLOR in kwargs:
            color = list(kwargs[ATTR_RGBWW_COLOR])
        else:
            color = list(self._scaled_color(self._num) or [255] * self._num)
            if not any(color):
                color = [255] * self._num

        # Apply brightness scaling.
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness or 255)
        scale = brightness / 255
        channels = [_to_fluval(round(c * scale)) for c in color]

        await self._device.async_set_channels(channels)
        if not self._device.status.on:
            await self._device.async_set_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.async_set_power(False)
