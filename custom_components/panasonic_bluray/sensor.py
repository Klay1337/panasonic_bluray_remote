"""Support for Panasonic Blu-ray player sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    ENTITY_ID_FORMAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Set up Panasonic Blu-ray sensor entities."""
    _LOGGER.debug("Panasonic async_add_entities sensors")
    coordinator = hass.data[DOMAIN][config_entry.entry_id][PANASONIC_COORDINATOR]

    entities = [
        PanasonicPositionSensor(coordinator, coordinator.name),
        PanasonicDeviceModeSensor(coordinator, coordinator.name),
        PanasonicPlaybackStateSensor(coordinator, coordinator.name),
        PanasonicSpeedSensor(coordinator, coordinator.name),
        PanasonicClockSensor(coordinator, coordinator.name),
    ]

    async_add_entities(entities)


class PanasonicSensorBase(CoordinatorEntity[PanasonicCoordinator], SensorEntity):
    """Base class for Panasonic sensors."""

    def __init__(self, coordinator: PanasonicCoordinator, name: str, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._sensor_type = sensor_type
        self._unique_id = ENTITY_ID_FORMAT.format(f"{self.coordinator.api.host}_{sensor_type}")

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class PanasonicPositionSensor(PanasonicSensorBase):
    """Sensor showing current playback position."""

    _attr_icon = "mdi:timer-play"

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the position sensor."""
        super().__init__(coordinator, name, "position")
        self._attr_name = f"{name} Position"

    @property
    def native_value(self) -> str | None:
        """Return the playback position formatted as HH:MM:SS."""
        data = self.coordinator.data
        if not data:
            return None

        position = data.get("media_position", 0)
        if position is None or position == 0:
            return "00:00:00"

        hours = position // 3600
        minutes = (position % 3600) // 60
        seconds = position % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "position_seconds": data.get("media_position", 0),
        }


class PanasonicDeviceModeSensor(PanasonicSensorBase):
    """Sensor showing current device mode."""

    _attr_icon = "mdi:disc-player"

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the device mode sensor."""
        super().__init__(coordinator, name, "device_mode")
        self._attr_name = f"{name} Device Mode"

    @property
    def native_value(self) -> str | None:
        """Return the device mode."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("device_mode")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "device_mode_value": data.get("device_mode_value"),
            "raw_status": data.get("raw_status"),
        }


class PanasonicPlaybackStateSensor(PanasonicSensorBase):
    """Sensor showing current playback state from PST."""

    _attr_icon = "mdi:play-circle"

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the playback state sensor."""
        super().__init__(coordinator, name, "playback_state")
        self._attr_name = f"{name} Playback State"

    @property
    def native_value(self) -> str | None:
        """Return the playback state."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("playback_state")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "playback_state_value": data.get("playback_state_value"),
            "raw_pst": data.get("raw_pst"),
        }


class PanasonicSpeedSensor(PanasonicSensorBase):
    """Sensor showing current playback speed."""

    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the speed sensor."""
        super().__init__(coordinator, name, "speed")
        self._attr_name = f"{name} Speed"

    @property
    def native_value(self) -> str | None:
        """Return the current speed as a human-readable string."""
        data = self.coordinator.data
        if not data:
            return None

        speed = data.get("speed_multiplier", 0)
        if speed is None:
            return None

        # Map speed values to human-readable names
        if speed == 0:
            return "Normal"
        elif 10 <= speed <= 14:
            return f"FF {speed - 9}"  # 10->FF1, 11->FF2, etc.
        elif 15 <= speed <= 18:
            return f"Slow {speed - 14}"  # 15->Slow1, 16->Slow2, etc.
        elif 20 <= speed <= 24:
            return f"REW {speed - 19}"  # 20->REW1, 21->REW2, etc.
        else:
            return f"Unknown ({speed})"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "speed_multiplier": data.get("speed_multiplier"),
        }


class PanasonicClockSensor(PanasonicSensorBase):
    """Sensor showing device clock time."""

    _attr_icon = "mdi:clock-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: PanasonicCoordinator, name: str) -> None:
        """Initialize the clock sensor."""
        super().__init__(coordinator, name, "clock")
        self._attr_name = f"{name} Clock"

    @property
    def native_value(self) -> str | None:
        """Return the device clock time."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("clock_time")
