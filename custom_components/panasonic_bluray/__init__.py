"""The panasonic_bluray remote and media player component."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST
from homeassistant.core import HomeAssistant

from .api import PanasonicBlurayAPI
from .const import (
    DOMAIN,
    DEFAULT_DEVICE_NAME,
    PANASONIC_COORDINATOR,
    STARTUP,
    PANASONIC_API,
    DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
)
from .coordinator import PanasonicCoordinator

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER.info(STARTUP)


PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Panasonic Blu-ray from a config entry."""
    panasonic_api = PanasonicBlurayAPI(entry.data[CONF_HOST])
    _LOGGER.debug("Panasonic device initialization")

    # Get polling interval from options (or use default)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    update_interval = timedelta(seconds=scan_interval)

    coordinator = PanasonicCoordinator(
        hass, panasonic_api, DEFAULT_DEVICE_NAME, update_interval
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        PANASONIC_COORDINATOR: coordinator,
        PANASONIC_API: panasonic_api,
    }

    # Get initial device state
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update - reload the integration."""
    await hass.config_entries.async_reload(entry.entry_id)
