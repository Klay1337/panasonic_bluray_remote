"""Support for Panasonic Blu-ray player select entities."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity, ENTITY_ID_FORMAT
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PANASONIC_COORDINATOR, MANUFACTURER
from .coordinator import PanasonicCoordinator

_LOGGER = logging.getLogger(__name__)

# Speed options mapping: display name -> (command, speed_multiplier value)
SPEED_OPTIONS = {
    "REW 5": ("SEARCH_REV5", 24),
    "REW 4": ("SEARCH_REV4", 23),
    "REW 3": ("SEARCH_REV3", 22),
    "REW 2": ("SEARCH_REV2", 21),
    "REW 1": ("SEARCH_REV1", 20),
    "Normal": ("PLAYBACK", 0),
    "FF 1": ("SEARCH_FWD1", 10),
    "FF 2": ("SEARCH_FWD2", 11),
    "FF 3": ("SEARCH_FWD3", 12),
    "FF 4": ("SEARCH_FWD4", 13),
    "FF 5": ("SEARCH_FWD5", 14),
}

# Reverse mapping: speed_multiplier value -> display name
SPEED_VALUE_TO_NAME = {v[1]: k for k, v in SPEED_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic Blu-ray select entities."""
    _LOGGER.debug("Panasonic async_add_entities select")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][PANASONIC_COORDINATOR]

    async_add_entities([PanasonicSpeedSelect(coordinator, coordinator.name)])


class PanasonicSpeedSelect(CoordinatorEntity[PanasonicCoordinator], SelectEntity):
    """Select entity for controlling playback speed."""

    _attr_icon = "mdi:fast-forward"

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the speed select."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = f"{name} Speed"
        self._attr_options = list(SPEED_OPTIONS.keys())
        self._unique_id = ENTITY_ID_FORMAT.format(f"{self.coordinator.api.host}_speed_select")

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
    def current_option(self) -> str | None:
        """Return the current speed option."""
        data = self.coordinator.data
        if not data:
            return None

        speed = data.get("speed_multiplier", 0)
        if speed is None:
            return None

        # Map speed value to option name
        return SPEED_VALUE_TO_NAME.get(speed, "Normal")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def select_option(self, option: str) -> None:
        """Change the playback speed."""
        if option not in SPEED_OPTIONS:
            _LOGGER.warning("Invalid speed option: %s", option)
            return

        command, _ = SPEED_OPTIONS[option]
        success, code = self.coordinator.api.send_command(command)
        _LOGGER.debug(
            "Speed select %s -> %s: %s (code=%s)",
            option,
            command,
            "OK" if success else "FAIL",
            code,
        )
        self.schedule_update_ha_state()
