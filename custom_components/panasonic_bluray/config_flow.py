"""Config flow for Panasonic Blu-ray integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import PanasonicBlurayAPI
from .const import (
    DOMAIN,
    DEFAULT_DEVICE_NAME,
    DEFAULT_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


def validate_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    config = {}
    _LOGGER.debug("Panasonic device user input %s", user_input)
    panasonic_api = PanasonicBlurayAPI(user_input[CONF_HOST])
    status = panasonic_api.get_player_status()

    if status is None:
        config = {"error": f"Could not connect to Panasonic device at {user_input[CONF_HOST]}"}
        _LOGGER.error("Could not connect to Panasonic device at %s", user_input[CONF_HOST])

    config.update(user_input)
    return config


class PanasonicConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Panasonic Blu-ray."""

    VERSION = 1
    MINOR_VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    reauth_entry: ConfigEntry | None = None
    user_input: dict[str, Any] | None = None

    def __init__(self) -> None:
        """Initialize Panasonic Config Flow."""
        self.discovery_info: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return PanasonicOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None or user_input == {}:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        if self.user_input is None:
            self.user_input = user_input
        else:
            self.user_input.update(user_input)

        try:
            info = await self.hass.async_add_executor_job(validate_input, self.user_input)
            if info.get("error"):
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors,
                )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            if len(errors.keys()) == 0:
                await self.async_set_unique_id(self.user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=DEFAULT_DEVICE_NAME, data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class PanasonicOptionsFlowHandler(OptionsFlow):
    """Handle Panasonic options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Panasonic options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current value or default
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
