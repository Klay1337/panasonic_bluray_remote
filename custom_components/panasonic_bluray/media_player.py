"""Support for Panasonic Blu-ray players."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    ENTITY_ID_FORMAT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    PANASONIC_COORDINATOR,
    MANUFACTURER,
    ATTR_DEVICE_MODE,
    ATTR_PLAYBACK_STATE,
    ATTR_SPEED_MULTIPLIER,
    ATTR_CLOCK_TIME,
    ATTR_TRAY_OPEN,
)
from .coordinator import PanasonicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entity."""
    _LOGGER.debug("Panasonic async_add_entities media player")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][PANASONIC_COORDINATOR]
    async_add_entities([PanasonicBluRayMediaPlayer(coordinator, coordinator.name)])


class PanasonicBluRayMediaPlayer(CoordinatorEntity[PanasonicCoordinator], MediaPlayerEntity):
    """Representation of a Panasonic Blu-ray device."""

    _attr_icon = "mdi:disc-player"
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
    )

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the Panasonic Blu-ray device."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = name
        self._attr_state = MediaPlayerState.OFF
        self._attr_media_position = 0
        self._attr_media_duration = 0
        self._unique_id = ENTITY_ID_FORMAT.format(f"{self.coordinator.api.host}_MediaPlayer")

    @property
    def unique_id(self) -> str | None:
        """Return unique ID."""
        return self._unique_id

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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data
        if not data:
            return {}

        attrs = {}
        if data.get(ATTR_DEVICE_MODE):
            attrs[ATTR_DEVICE_MODE] = data.get(ATTR_DEVICE_MODE)
        if data.get(ATTR_PLAYBACK_STATE):
            attrs[ATTR_PLAYBACK_STATE] = data.get(ATTR_PLAYBACK_STATE)
        if data.get(ATTR_SPEED_MULTIPLIER) is not None:
            attrs[ATTR_SPEED_MULTIPLIER] = data.get(ATTR_SPEED_MULTIPLIER)
        if data.get(ATTR_CLOCK_TIME):
            attrs[ATTR_CLOCK_TIME] = data.get(ATTR_CLOCK_TIME)
        if data.get(ATTR_TRAY_OPEN) is not None:
            attrs[ATTR_TRAY_OPEN] = data.get(ATTR_TRAY_OPEN)

        return attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_data()
        self.async_write_ha_state()

    def _update_from_data(self) -> None:
        """Update the internal state from coordinator data."""
        data = self.coordinator.data
        self._attr_state = data.get("state")
        self._attr_media_position = data.get("media_position")
        self._attr_media_position_updated_at = data.get("media_position_updated_at")
        self._attr_media_duration = data.get("media_duration")

    def turn_off(self) -> None:
        """Instruct the device to turn to standby.

        Sending the "POWEROFF" command will turn the device to standby - there
        is no way to turn it completely off remotely. However this works in
        our favour as it means the device is still accepting commands and we
        can thus turn it back on when desired.
        """
        if self._attr_state != MediaPlayerState.OFF:
            self.coordinator.api.power_off()
        self._attr_state = MediaPlayerState.OFF

    def turn_on(self) -> None:
        """Wake the device back up from standby."""
        if self._attr_state == MediaPlayerState.OFF:
            self.coordinator.api.power_on()
        self._attr_state = MediaPlayerState.IDLE

    def media_play(self) -> None:
        """Send play command."""
        self.coordinator.api.play()
        self.schedule_update_ha_state()

    def media_pause(self) -> None:
        """Send pause command."""
        self.coordinator.api.pause()
        self.schedule_update_ha_state()

    def media_stop(self) -> None:
        """Send stop command."""
        self.coordinator.api.stop()
        self.schedule_update_ha_state()

    def media_next_track(self) -> None:
        """Send next track command."""
        self.coordinator.api.next_track()
        self.schedule_update_ha_state()

    def media_previous_track(self) -> None:
        """Send the previous track command."""
        self.coordinator.api.previous_track()
        self.schedule_update_ha_state()
