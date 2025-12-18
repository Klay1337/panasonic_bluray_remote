"""Data update coordinator for Panasonic Blu-ray integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import utcnow

from .api import PanasonicBlurayAPI, DeviceMode, PlaybackState
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PanasonicCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for Panasonic Blu-ray player."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: PanasonicBlurayAPI,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=update_interval,
        )
        self.hass = hass
        self.name = name
        self.api = api
        self.data = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Panasonic device."""
        _LOGGER.debug("Panasonic device coordinator update")
        try:
            self.data = await self.hass.async_add_executor_job(self._update)
            return self.data
        except Exception as ex:
            _LOGGER.error("Panasonic device coordinator error during update: %s", ex)
            raise UpdateFailed(
                f"Error communicating with Panasonic device API: {ex}"
            ) from ex

    def _update(self) -> dict[str, Any]:
        """Update the internal state by querying the device."""
        data = {}

        # Get comprehensive player status
        status = self.api.get_player_status()

        if status is None:
            data["state"] = None
            data["is_on"] = None
            data["device_mode"] = None
            data["playback_state"] = None
            data["media_position"] = 0
            data["media_duration"] = 0
            data["speed_multiplier"] = 0
            data["tray_open"] = None
            data["clock_time"] = None
            return data

        # Power state
        data["is_on"] = status.is_on

        # Device mode (raw enum value)
        data["device_mode"] = status.device_mode.name
        data["device_mode_value"] = status.device_mode.value

        # Playback state (raw enum value)
        data["playback_state"] = status.playback_state.name
        data["playback_state_value"] = status.playback_state.value

        # Map to Home Assistant MediaPlayerState
        if not status.is_on:
            data["state"] = MediaPlayerState.OFF
        elif status.device_mode == DeviceMode.TRAY_OPEN:
            data["state"] = MediaPlayerState.IDLE
        elif status.device_mode == DeviceMode.IDLE:
            data["state"] = MediaPlayerState.IDLE
        elif status.device_mode == DeviceMode.PLAYING:
            data["state"] = MediaPlayerState.PLAYING
        elif status.device_mode == DeviceMode.PAUSED:
            data["state"] = MediaPlayerState.PAUSED
        elif status.device_mode in (DeviceMode.FAST_FORWARD, DeviceMode.REWIND, DeviceMode.SLOW_MOTION):
            # Treat seeking modes as playing
            data["state"] = MediaPlayerState.PLAYING
        else:
            data["state"] = MediaPlayerState.IDLE

        # Position and duration
        data["media_position"] = status.position_seconds
        data["media_position_updated_at"] = utcnow()
        data["media_duration"] = 0  # Duration not reliably available

        # Speed
        data["speed_multiplier"] = status.speed_multiplier

        # Tray state
        data["tray_open"] = status.device_mode == DeviceMode.TRAY_OPEN

        # Clock time
        data["clock_time"] = status.clock_time

        # Raw data for debugging
        data["raw_pst"] = status.raw_pst
        data["raw_status"] = status.raw_status

        return data
