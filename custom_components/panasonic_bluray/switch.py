"""Support for Panasonic Blu-ray player tray switch."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, ENTITY_ID_FORMAT
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PANASONIC_COORDINATOR, MANUFACTURER
from .coordinator import PanasonicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic Blu-ray switch entities."""
    _LOGGER.debug("Panasonic async_add_entities switch")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][PANASONIC_COORDINATOR]
    async_add_entities([PanasonicTraySwitch(coordinator, coordinator.name)])


class PanasonicTraySwitch(CoordinatorEntity[PanasonicCoordinator], SwitchEntity):
    """Representation of the Panasonic Blu-ray disc tray."""

    _attr_icon = "mdi:disc"

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the tray switch."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_name = f"{name} Tray"
        self._unique_id = ENTITY_ID_FORMAT.format(f"{self.coordinator.api.host}_Tray")
        self._attr_is_on = False

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
    def is_on(self) -> bool | None:
        """Return true if the tray is open."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("tray_open")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    def turn_on(self, **kwargs) -> None:
        """Open the disc tray."""
        self.coordinator.api.open_tray()
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs) -> None:
        """Close the disc tray."""
        self.coordinator.api.close_tray()
        self.schedule_update_ha_state()
