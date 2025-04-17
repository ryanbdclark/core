"""Test helpers for Owlet integration."""

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from homeassistant.components.owlet.const import (
    CONF_OWLET_EXPIRY,
    CONF_OWLET_REFRESH,
    DOMAIN,
)
from homeassistant.const import CONF_API_TOKEN, CONF_EMAIL, CONF_REGION

from .const import API_KEY, EMAIL, EXPIRY, REFRESH, REGION

from tests.common import MockConfigEntry, load_fixture


@pytest_asyncio.fixture
async def mock_owlet_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=EMAIL,
        data={
            CONF_REGION: REGION,
            CONF_EMAIL: EMAIL,
            CONF_API_TOKEN: API_KEY,
            CONF_OWLET_REFRESH: REFRESH,
            CONF_OWLET_EXPIRY: EXPIRY,
        },
        minor_version=1,
        entry_id="01JS1B1KH82GN4MD5N7VWECMY2",
        unique_id=EMAIL.lower(),
    )


@pytest.fixture(autouse=True)
def mock_owlet_api(request: pytest.FixtureRequest):
    """Fixture to provide a OwletAPI."""
    props_file = getattr(request, "param", {}).get(
        "properties", "update_properties_charging.json"
    )
    devices_file = getattr(request, "param", {}).get("devices", "get_devices.json")

    mock_owlet_api = AsyncMock()
    mock_owlet_api.expiry = EXPIRY
    mock_owlet_api.authenticate.return_value = None
    mock_owlet_api.get_properties.return_value = json.loads(
        load_fixture(props_file, "owlet")
    )
    mock_owlet_api.get_devices.return_value = json.loads(
        load_fixture(devices_file, "owlet")
    )

    with (
        patch("homeassistant.components.owlet.OwletAPI", return_value=mock_owlet_api),
        patch(
            "homeassistant.components.owlet.config_flow.OwletAPI",
            return_value=mock_owlet_api,
        ),
    ):
        yield mock_owlet_api


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.owlet.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
