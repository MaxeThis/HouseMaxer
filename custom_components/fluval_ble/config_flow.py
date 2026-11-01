"""Config flow for Fluval BLE Light."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import CONF_CHANNELS, DEFAULT_CHANNELS, DOMAIN

# Vendor MAC prefixes seen on Fluval / Inledco controllers.
KNOWN_PREFIXES = ("44:A6:E5", "B8:80:4F")


def _looks_like_fluval(info: BluetoothServiceInfoBleak) -> bool:
    addr = info.address.upper()
    if any(addr.startswith(p) for p in KNOWN_PREFIXES):
        return True
    name = (info.name or "").lower()
    return any(k in name for k in ("fluval", "aquasky", "plant", "marine"))


class FluvalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fluval BLE Light."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a flow started from auto-discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if not _looks_like_fluval(discovery_info):
            return self.async_abort(reason="not_supported")
        self._discovered_address = discovery_info.address
        self._discovered_name = discovery_info.name or discovery_info.address
        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_configure()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow started by the user: pick a nearby device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._discovered_address = address
            self._discovered_name = self._device_choices().get(address, address)
            return await self.async_step_configure()

        choices: dict[str, str] = self._device_choices()
        if not choices:
            return self.async_abort(reason="no_devices_found")

        schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(choices)})
        return self.async_show_form(step_id="user", data_schema=schema)

    def _device_choices(self) -> dict[str, str]:
        """All nearby connectable BLE devices, Fluval-looking ones first."""
        infos = list(bluetooth.async_discovered_service_info(self.hass, connectable=True))
        infos.sort(key=lambda i: (not _looks_like_fluval(i), i.address))
        configured = self._async_current_ids()
        choices: dict[str, str] = {}
        for info in infos:
            if info.address in configured:
                continue
            label = info.name or "Unknown"
            tag = " ★" if _looks_like_fluval(info) else ""
            choices[info.address] = f"{label} ({info.address}){tag}"
        return choices

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick the channel count and finish."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or "Fluval Light",
                data={
                    CONF_ADDRESS: self._discovered_address,
                    CONF_CHANNELS: user_input[CONF_CHANNELS],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_CHANNELS, default=DEFAULT_CHANNELS): vol.In(
                    {4: "4 channels (RGBW — Flex, Aquasky)", 5: "5 channels (Plant, Marine)"}
                )
            }
        )
        return self.async_show_form(
            step_id="configure",
            data_schema=schema,
            description_placeholders={"name": self._discovered_name or ""},
        )
