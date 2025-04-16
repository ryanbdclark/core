"""Provides diagnostics for Fyta."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_OWLET_REFRESH
from .coordinator import OwletConfigEntry

TO_REDACT = [CONF_USERNAME, CONF_API_TOKEN, CONF_OWLET_REFRESH]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: OwletConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    return {
        "config_entry": async_redact_data(config_entry.as_dict(), TO_REDACT),
    }
