"""Support for Panasonic Blu-ray remote entity."""
from __future__ import annotations

import logging
import time
from typing import Any, Iterable

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.components.remote import (
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
    RemoteEntityFeature,
    ENTITY_ID_FORMAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import PANASONIC_COORDINATOR, DOMAIN, MANUFACTURER
from .coordinator import PanasonicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic Blu-ray remote entity."""
    _LOGGER.debug("Panasonic async_add_entities remote")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][PANASONIC_COORDINATOR]
    async_add_entities([PanasonicBluRayRemote(coordinator, coordinator.name)])


class PanasonicBluRayRemote(CoordinatorEntity[PanasonicCoordinator], RemoteEntity):
    """Representation of a Panasonic Blu-ray remote."""

    _attr_icon = "mdi:remote"
    _attr_supported_features: RemoteEntityFeature = RemoteEntityFeature(0)

    # All available commands that can be sent via remote.send_command
    AVAILABLE_COMMANDS = [
        # Power
        "POWER", "POWERON", "POWEROFF",
        # Playback
        "PLAY", "PLAYBACK", "PAUSE", "STOP",
        "MEDIA_PLAY", "MEDIA_PAUSE", "MEDIA_PLAY_PAUSE", "MEDIA_STOP",
        # Navigation
        "UP", "DOWN", "LEFT", "RIGHT", "SELECT", "OK", "RETURN", "BACK",
        "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "DPAD_CENTER",
        "EXIT", "HOME", "MENU", "TITLE", "POPUP", "PUPMENU", "SETUP",
        # Skip / Chapter
        "SKIPFWD", "SKIPREV", "NEXT", "PREV", "PREVIOUS",
        "MEDIA_NEXT", "MEDIA_PREVIOUS",
        # Fast Forward
        "CUE", "FF",
        "SEARCH_FWD1", "SEARCH_FWD2", "SEARCH_FWD3", "SEARCH_FWD4", "SEARCH_FWD5",
        # Rewind
        "REV", "REW",
        "SEARCH_REV1", "SEARCH_REV2", "SEARCH_REV3", "SEARCH_REV4", "SEARCH_REV5",
        # Slow Motion
        "SLOW_FWD1", "SLOW_FWD2", "SLOW_FWD3", "SLOW_FWD4", "SLOW_FWD5",
        # Frame Advance
        "FRAMEADV", "REVERSEFRAMEADV",
        # Tray
        "OP_CL", "EJECT", "TRAYOPEN", "TRAYCLOSE",
        # Color buttons
        "RED", "GREEN", "YELLOW", "BLUE",
        # Numbers
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9",
        # Audio/Video settings
        "AUDIOSEL", "AUDIO", "SUB_TITLE", "SUBTITLE", "DETAIL", "INFO",
        "DSPSEL", "DISPLAY", "OSDONOFF", "3D", "PICTMD",
        "PICTURESETTINGS", "HDR_PICTUREMODE",
        # Apps
        "NETFLIX", "NETWORK", "MIRACAST",
    ]

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the Panasonic Blu-ray remote entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = f"{name} Remote"
        self._state: MediaPlayerState | None = None
        self._unique_id = ENTITY_ID_FORMAT.format(f"{self.coordinator.api.host}_Remote")

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.host)},
            name=self.coordinator.name,
            manufacturer=MANUFACTURER,
            model="Blu-ray Player",
        )

    @property
    def unique_id(self) -> str | None:
        """Return unique ID."""
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is on."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("is_on")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def turn_off(self) -> None:
        """Turn the device to standby."""
        self.coordinator.api.power_off()

    def turn_on(self) -> None:
        """Wake the device from standby."""
        self.coordinator.api.power_on()

    def toggle(self, activity: str | None = None, **kwargs: Any) -> None:
        """Toggle the device power."""
        self.coordinator.api.send_command("POWER")

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to the device.

        Available commands include:
        - Power: POWER, POWERON, POWEROFF
        - Playback: PLAY, PAUSE, STOP
        - Navigation: UP, DOWN, LEFT, RIGHT, SELECT, OK, RETURN, MENU, HOME, etc.
        - Skip: SKIPFWD, SKIPREV, NEXT, PREV
        - Speed: CUE, REV, SEARCH_FWD1-5, SEARCH_REV1-5, SLOW_FWD1-5
        - Tray: EJECT, TRAYOPEN, TRAYCLOSE, OP_CL
        - Numbers: 0-9 or D0-D9
        - Colors: RED, GREEN, YELLOW, BLUE
        - Audio/Video: AUDIO, SUBTITLE, INFO, DISPLAY, 3D, HDR_PICTUREMODE
        - Apps: NETFLIX, NETWORK, MIRACAST
        """
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)

        for _ in range(num_repeats):
            for single_command in command:
                success, code = self.coordinator.api.send_command(single_command)
                _LOGGER.debug(
                    "send_command %s: %s (code=%s)",
                    single_command,
                    "OK" if success else "FAIL",
                    code,
                )
                time.sleep(delay_secs)
