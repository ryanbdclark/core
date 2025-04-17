"""Test Fyta diagnostics."""

from syrupy import SnapshotAssertion
from syrupy.filters import props

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import setup_platform

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]


async def test_entry_diagnostics(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test config entry diagnostics."""
    await setup_platform(hass, mock_owlet_entry, PLATFORMS)

    result = await get_diagnostics_for_config_entry(hass, hass_client, mock_owlet_entry)
    assert result == snapshot(exclude=props("created_at", "modified_at"))
