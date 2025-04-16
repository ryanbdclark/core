"""Config flow for Owlet Smart Sock integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, cast

from pyowletapi.api import OwletAPI
from pyowletapi.exceptions import OwletCredentialsError, OwletDevicesError
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION): vol.In(["europe", "world"]),
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_REAUTH_RECONFIG_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})


class OwletConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Owlet Smart Sock."""

    VERSION = 1
    reauth_entry: ConfigEntry | None = None

    def __init__(self) -> None:
        """Initialise config flow."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            owlet_api = OwletAPI(
                region=user_input[CONF_REGION],
                user=user_input[CONF_EMAIL],
                password=user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
            )

            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()

            try:
                token = await owlet_api.authenticate()
                await owlet_api.validate_authentication()

            except OwletDevicesError:
                errors["base"] = "no_devices"
            except OwletCredentialsError:
                errors["base"] = "invalid_credentials"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                entry_data = {
                    CONF_REGION: user_input[CONF_REGION],
                    CONF_EMAIL: user_input[CONF_EMAIL],
                }
                if token is not None:
                    entry_data.update(token)

                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=entry_data,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, user_input: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        assert self.reauth_entry is not None
        errors: dict[str, str] = {}

        if user_input is not None:
            entry_data = self.reauth_entry.data
            owlet_api = OwletAPI(
                entry_data[CONF_REGION],
                entry_data[CONF_EMAIL],
                user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
            )
            try:
                if token := await owlet_api.authenticate():
                    self.hass.config_entries.async_update_entry(
                        self.reauth_entry, data={**entry_data, **token}
                    )

                    await self.hass.config_entries.async_reload(
                        self.reauth_entry.entry_id
                    )

                    return self.async_abort(reason="reauth_successful")

            except OwletCredentialsError:
                errors["base"] = "invalid_credentials"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error reauthenticating")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_RECONFIG_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that allows the user to reconfigure the integration."""
        errors: dict[str, str] = {}

        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            owlet_api = OwletAPI(
                str(reconfigure_entry.data.get(CONF_REGION)),
                str(reconfigure_entry.data.get(CONF_EMAIL)),
                user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
            )
            try:
                if token := await owlet_api.authenticate():
                    email = cast(str, reconfigure_entry.data.get(CONF_EMAIL))
                    await self.async_set_unique_id(email.lower())
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data_updates={
                            **token,
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                        },
                    )
            except OwletDevicesError:
                errors["base"] = "no_devices"
            except OwletCredentialsError:
                errors["base"] = "invalid_credentials"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=STEP_REAUTH_RECONFIG_SCHEMA,
            errors=errors,
        )


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
