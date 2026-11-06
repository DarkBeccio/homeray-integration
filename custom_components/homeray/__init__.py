"""Homeray: health checks and network discovery for the Homeray dashboard cards."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .analysis import low_batteries, silent_devices
from .const import DEFAULTS, DOMAIN, UPDATE_INTERVAL
from .network import discover

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

type HomerayConfigEntry = ConfigEntry[HomerayCoordinator]


def entry_options(entry: ConfigEntry) -> dict[str, Any]:
    return {**DEFAULTS, **entry.options}


class HomerayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Runs the checks every few minutes; they only read Home Assistant's own data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    def snapshot(self) -> dict[str, Any]:
        opts = entry_options(self.config_entry)
        return {"silent": silent_devices(self.hass, opts), "batteries": low_batteries(self.hass, opts), "options": opts}

    async def _async_update_data(self) -> dict[str, Any]:
        return self.snapshot()


async def async_setup_entry(hass: HomeAssistant, entry: HomerayConfigEntry) -> bool:
    coordinator = HomerayCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    _register_ws(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: HomerayConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _coordinator(hass: HomeAssistant) -> HomerayCoordinator | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        return entry.runtime_data
    return None


@callback
def _register_ws(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_ws"):
        return
    hass.data[f"{DOMAIN}_ws"] = True
    websocket_api.async_register_command(hass, ws_status)
    websocket_api.async_register_command(hass, ws_network)


@websocket_api.websocket_command({vol.Required("type"): "homeray/status"})
@callback
def ws_status(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Silent devices and low batteries, computed now."""
    coord = _coordinator(hass)
    if coord is None:
        connection.send_error(msg["id"], "not_loaded", "Homeray is not set up")
        return
    connection.send_result(msg["id"], {"version": 1, **coord.snapshot()})


@websocket_api.websocket_command({vol.Required("type"): "homeray/network"})
@callback
def ws_network(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Floors and network devices for the map card."""
    if _coordinator(hass) is None:
        connection.send_error(msg["id"], "not_loaded", "Homeray is not set up")
        return
    connection.send_result(msg["id"], {"version": 1, **discover(hass)})
