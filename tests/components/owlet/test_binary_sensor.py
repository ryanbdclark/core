"""Test Owlet Sensor."""

from __future__ import annotations

import pytest
from syrupy import SnapshotAssertion

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_platform

from tests.common import MockConfigEntry, snapshot_platform


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [{"properties": "update_properties_asleep.json", "devices": "get_devices.json"}],
    indirect=True,
)
async def test_sensors_asleep(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test sensor values."""
    await setup_platform(hass, mock_owlet_entry, [Platform.BINARY_SENSOR])
    await snapshot_platform(hass, entity_registry, snapshot, mock_owlet_entry.entry_id)


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [{"properties": "update_properties_awake.json", "devices": "get_devices.json"}],
    indirect=True,
)
async def test_sensors_awake(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test sensor values."""
    await setup_platform(hass, mock_owlet_entry, [Platform.BINARY_SENSOR])
    await snapshot_platform(hass, entity_registry, snapshot, mock_owlet_entry.entry_id)


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [{"properties": "update_properties_charging.json", "devices": "get_devices.json"}],
    indirect=True,
)
async def test_sensors_charging(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test sensor values."""
    await setup_platform(hass, mock_owlet_entry, [Platform.BINARY_SENSOR])
    await snapshot_platform(hass, entity_registry, snapshot, mock_owlet_entry.entry_id)


@pytest.mark.parametrize(
    "mock_owlet_entry",
    [{"properties": "update_properties_v2.json", "devices": "get_devices.json"}],
    indirect=True,
)
async def test_sensors_v2(
    hass: HomeAssistant,
    mock_owlet_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test sensor values."""
    await setup_platform(hass, mock_owlet_entry, [Platform.BINARY_SENSOR])
    await snapshot_platform(hass, entity_registry, snapshot, mock_owlet_entry.entry_id)
