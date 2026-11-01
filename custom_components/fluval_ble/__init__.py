"""The Fluval BLE Light integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import CONF_CHANNELS, DEFAULT_CHANNELS, DOMAIN
from .fluval import FluvalDevice
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SELECT]

SERVICE_SET_AUTO_SCHEDULE = "set_auto_schedule"


def _to_minutes(value) -> int:
    """Accept 'HH:MM', 'HH:MM:SS', or an int number of minutes."""
    if isinstance(value, (int, float)):
        return int(value)
    parts = str(value).split(":")
    h = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 else 0
    return h * 60 + m


SCHEDULE_SCHEMA = vol.Schema(
    {
        vol.Optional("address"): cv.string,
        vol.Required("sunrise_start"): vol.Any(cv.string, vol.Coerce(int)),
        vol.Required("sunrise_end"): vol.Any(cv.string, vol.Coerce(int)),
        vol.Required("sunset_start"): vol.Any(cv.string, vol.Coerce(int)),
        vol.Required("sunset_end"): vol.Any(cv.string, vol.Coerce(int)),
        vol.Required("day"): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Required("night"): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional("turnoff"): vol.Any(cv.string, vol.Coerce(int)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fluval BLE Light from a config entry."""
    address: str = entry.data["address"]
    num_channels: int = entry.data.get(CONF_CHANNELS, DEFAULT_CHANNELS)

    def _ble_device():
        return bluetooth.async_ble_device_from_address(hass, address, connectable=True)

    if _ble_device() is None:
        raise ConfigEntryNotReady(
            f"Fluval light {address} not found by any Bluetooth adapter yet"
        )

    device = FluvalDevice(_ble_device, num_channels=num_channels, address=address)
    try:
        await device.connect()
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(f"Could not connect to Fluval light: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration-wide services (once)."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_AUTO_SCHEDULE):
        return

    async def _handle_set_auto_schedule(call: ServiceCall) -> None:
        devices: dict = hass.data.get(DOMAIN, {})
        if not devices:
            raise HomeAssistantError("No Fluval light is set up")
        address = call.data.get("address")
        targets = [
            d
            for d in devices.values()
            if address is None or d.mac.upper() == address.upper()
        ]
        if not targets:
            raise HomeAssistantError(f"No Fluval light matching address {address}")

        turnoff = call.data.get("turnoff")
        turnoff_min = (
            None
            if turnoff in (None, "", "off", "none")
            else _to_minutes(turnoff)
        )
        for device in targets:
            await device.async_set_auto_schedule(
                sunrise_start=_to_minutes(call.data["sunrise_start"]),
                sunrise_end=_to_minutes(call.data["sunrise_end"]),
                day=list(call.data["day"]),
                sunset_start=_to_minutes(call.data["sunset_start"]),
                sunset_end=_to_minutes(call.data["sunset_end"]),
                night=list(call.data["night"]),
                turnoff=turnoff_min,
            )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_AUTO_SCHEDULE,
        _handle_set_auto_schedule,
        schema=SCHEDULE_SCHEMA,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        device: FluvalDevice = hass.data[DOMAIN].pop(entry.entry_id)
        await device.disconnect()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_AUTO_SCHEDULE)
    return unload_ok
