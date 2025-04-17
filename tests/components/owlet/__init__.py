"""Tests for the Owlet integration."""

from unittest.mock import patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def setup_platform(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platforms: list[Platform],
    setup: bool = True,
) -> MockConfigEntry:
    """Set up the Owlet platforms."""
    config_entry.add_to_hass(hass)
    if setup:
        with patch("homeassistant.components.owlet.PLATFORMS", platforms):
            await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
