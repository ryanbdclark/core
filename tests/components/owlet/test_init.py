"""Test the initialization."""

from datetime import timedelta
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletCredentialsError,
    OwletDevicesError,
)
import pytest

from homeassistant.components.owlet.const import CONF_OWLET_EXPIRY, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import setup_platform
from .const import AUTH_RETURN, EXPIRY, EXPIRY_OLD

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_load_unload(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
) -> None:
    """Test load and unload."""

    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    assert mock_owlet_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_owlet_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_owlet_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [
        {
            "properties": "update_properties_asleep.json",
            "devices": "get_devices_with_tokens.json",
        }
    ],
    indirect=True,
)
async def test_authenticate_returns_tokens(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    mock_owlet_api: AsyncMock,
) -> None:
    """Test we refresh an expired token."""
    mock_owlet_api.expiry = EXPIRY_OLD
    mock_owlet_api.authenticate.return_value = AUTH_RETURN
    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    assert mock_owlet_entry.state is ConfigEntryState.LOADED

    assert mock_owlet_entry.data[CONF_OWLET_EXPIRY] == EXPIRY


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [
        {
            "properties": "update_properties_asleep.json",
            "devices": "get_devices_with_tokens.json",
        }
    ],
    indirect=True,
)
async def test_refresh_expired_token(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    mock_owlet_api: AsyncMock,
) -> None:
    """Test we refresh an expired token."""

    mock_owlet_api.expiry = EXPIRY_OLD
    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    assert mock_owlet_entry.state is ConfigEntryState.LOADED

    assert mock_owlet_entry.data[CONF_OWLET_EXPIRY] == EXPIRY


@pytest.mark.parametrize(
    "exception",
    [
        OwletAuthenticationError,
        OwletCredentialsError,
    ],
)
async def test_invalid_credentials(
    hass: HomeAssistant,
    exception: Exception,
    mock_owlet_entry: MockConfigEntry,
    mock_owlet_api: AsyncMock,
) -> None:
    """Test Owlet credentials changing."""

    mock_owlet_api.expiry = EXPIRY_OLD
    mock_owlet_api.authenticate.side_effect = exception

    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    assert mock_owlet_entry.state is ConfigEntryState.SETUP_ERROR


@pytest.mark.parametrize(
    "exception",
    [
        OwletDevicesError,
    ],
)
async def test_no_devices(
    hass: HomeAssistant,
    exception: Exception,
    mock_owlet_entry: MockConfigEntry,
    mock_owlet_api: AsyncMock,
) -> None:
    """Test when there are no devices on the account."""

    mock_owlet_api.get_devices.side_effect = exception

    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    assert mock_owlet_entry.state is ConfigEntryState.SETUP_ERROR


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [
        {
            "properties": "update_properties_asleep.json",
            "devices": "get_devices_with_tokens.json",
        }
    ],
    indirect=True,
)
async def test_devices_returns_tokens(
    hass: HomeAssistant, mock_owlet_entry: MockConfigEntry, mock_owlet_api: AsyncMock
) -> None:
    """Test we update tokens when returned from API."""
    mock_owlet_api.expiry = EXPIRY_OLD
    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    assert mock_owlet_entry.state is ConfigEntryState.LOADED

    assert mock_owlet_entry.data[CONF_OWLET_EXPIRY] == EXPIRY


async def test_raise_config_entry_not_ready_when_offline(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    mock_owlet_api: AsyncMock,
) -> None:
    """Config entry state is SETUP_RETRY when Owlet is offline."""

    mock_owlet_api.get_properties.side_effect = OwletConnectionError

    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    assert mock_owlet_entry.state is ConfigEntryState.SETUP_RETRY

    assert len(hass.config_entries.flow.async_progress()) == 0


async def test_raise_config_entry_not_ready_when_offline_and_expired(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    mock_owlet_api: AsyncMock,
) -> None:
    """Config entry state is SETUP_RETRY when Owlet is offline and access_token is expired."""

    mock_owlet_api.authenticate.side_effect = OwletConnectionError
    mock_owlet_api.expiration = EXPIRY_OLD

    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])
    await hass.async_block_till_done()

    assert mock_owlet_entry.state is ConfigEntryState.SETUP_RETRY

    assert len(hass.config_entries.flow.async_progress()) == 0


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [
        {
            "properties": "update_properties_asleep.json",
            "devices": "get_devices_with_tokens.json",
        }
    ],
    indirect=True,
)
async def test_remove_stale_sock(
    hass: HomeAssistant,
    mock_owlet_api: AsyncMock,
    mock_owlet_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Ensure stale scale is cleaned up."""

    await setup_platform(hass, mock_owlet_entry, [Platform.SENSOR])

    device = device_registry.async_get_device(identifiers={(DOMAIN, "SERIAL_NUMBER")})
    assert device

    mock_owlet_api.get_devices.return_value = {"response": {}}

    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, "SERIAL_NUMBER")})
    assert device is None
