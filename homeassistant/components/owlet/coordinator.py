"""Owlet integration coordinator class."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

from pyowletapi.const import Properties
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletError,
)
from pyowletapi.sock import Sock

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)

type OwletConfigEntry = ConfigEntry[dict[str, OwletCoordinator]]


@dataclass(slots=True)
class UpdateCoordinatorDataType:
    """Update coordinator data type."""

    sensors: Properties


class OwletCoordinator(DataUpdateCoordinator[UpdateCoordinatorDataType]):
    """Coordinator is responsible for querying the device at a specified route."""

    def __init__(self, hass: HomeAssistant, sock: Sock, entry: ConfigEntry) -> None:
        """Initialise a custom coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLLING_INTERVAL),
        )
        self.sock = sock
        self.config_entry: ConfigEntry = entry

    async def _async_update_data(
        self,
    ) -> UpdateCoordinatorDataType:
        """Fetch the data from the device."""
        try:
            await self._check_for_stale_devices()
            properties = await self.sock.update_properties()
            if "tokens" in properties:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **properties["tokens"]},
                )
        except OwletAuthenticationError as auth_err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.config_entry.data[CONF_EMAIL]}"
            ) from auth_err
        except (OwletError, OwletConnectionError) as conn_err:
            raise UpdateFailed(
                f"Unable to connect to Owlet servers: {conn_err}"
            ) from conn_err
        else:
            return UpdateCoordinatorDataType(properties["properties"])

    async def _check_for_stale_devices(self) -> None:
        """Check if the device is stale, missing from Owlet API response."""
        devices = await self.sock.api.get_devices()
        current_socks = [device["device"]["dsn"] for device in devices["response"]]
        if self.sock.serial not in current_socks:
            _LOGGER.debug(
                "Device %s no longer present in Owlet device list, removing stale device",
                self.sock.serial,
            )
            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)

            device = device_registry.async_get_device({(DOMAIN, self.sock.serial)})
            if device:
                for entity in er.async_entries_for_device(entity_registry, device.id):
                    entity_registry.async_remove(entity.entity_id)

                device_registry.async_remove_device(device.id)

            coordinators = self.config_entry.runtime_data
            coordinators.pop(self.sock.serial, None)
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self.config_entry.entry_id)
            )
            raise UpdateFailed(f"Device {self.sock.serial} no longer exists")
