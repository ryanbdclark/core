"""Test Owlet config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pyowletapi.exceptions import OwletCredentialsError, OwletDevicesError
import pytest

from homeassistant import config_entries
from homeassistant.components.owlet.const import (
    CONF_OWLET_EXPIRY,
    CONF_OWLET_REFRESH,
    DOMAIN,
)
from homeassistant.const import CONF_API_TOKEN, CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import (
    API_KEY,
    AUTH_RETURN,
    EMAIL,
    EXPIRY,
    PASSWORD,
    REAUTH_RETURN,
    REFRESH,
    REGION,
)

from tests.common import MockConfigEntry


async def user_step(
    hass: HomeAssistant, flow_id: str, mock_setup_entry: AsyncMock
) -> None:
    """Test user step (helper function)."""

    result = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_REGION: REGION, CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == EMAIL
    assert result["data"] == {
        CONF_REGION: REGION,
        CONF_EMAIL: EMAIL,
        CONF_API_TOKEN: API_KEY,
        CONF_OWLET_REFRESH: REFRESH,
        CONF_OWLET_EXPIRY: EXPIRY,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_flow(
    hass: HomeAssistant, mock_owlet_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    mock_owlet_api.authenticate.return_value = AUTH_RETURN
    await user_step(hass, result["flow_id"], mock_setup_entry)


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (OwletDevicesError, {"base": "no_devices"}),
        (OwletCredentialsError, {"base": "invalid_credentials"}),
        (Exception, {"base": "unknown"}),
    ],
)
async def test_form_exceptions(
    hass: HomeAssistant,
    exception: Exception,
    error: dict[str, str],
    mock_owlet_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we can handle Form exceptions."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_owlet_api.authenticate.side_effect = exception

    # tests with connection error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: REGION, CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == error

    mock_owlet_api.authenticate.side_effect = None
    mock_owlet_api.authenticate.return_value = AUTH_RETURN

    # tests with all information provided
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: REGION, CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == EMAIL
    assert result["data"][CONF_REGION] == REGION
    assert result["data"][CONF_EMAIL] == EMAIL
    assert result["data"][CONF_API_TOKEN] == API_KEY
    assert result["data"][CONF_OWLET_EXPIRY] == EXPIRY
    assert result["data"][CONF_OWLET_REFRESH] == REFRESH

    assert len(mock_setup_entry.mock_calls) == 1


async def test_duplicate_entry(
    hass: HomeAssistant, mock_owlet_api: AsyncMock, mock_owlet_entry: MockConfigEntry
) -> None:
    """Test duplicate setup handling."""

    mock_owlet_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    mock_owlet_api.authenticate.return_value = AUTH_RETURN
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_REGION: REGION, CONF_EMAIL: EMAIL, CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_flow(
    hass: HomeAssistant,
    mock_owlet_api: AsyncMock,
    mock_owlet_entry: MockConfigEntry,
) -> None:
    """Test that the reauth flow."""

    mock_owlet_entry.add_to_hass(hass)

    result = await mock_owlet_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    mock_owlet_api.authenticate.return_value = REAUTH_RETURN
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_password"},
    )

    assert result2["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    assert result2["reason"] == "reauth_successful"
    assert mock_owlet_entry.data[CONF_API_TOKEN] == REAUTH_RETURN[CONF_API_TOKEN]


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (OwletCredentialsError, {"base": "invalid_credentials"}),
        (Exception, {"base": "unknown"}),
    ],
)
async def test_reauth_flow_errors(
    hass: HomeAssistant,
    exception: Exception,
    error: dict[str, str],
    mock_owlet_api: AsyncMock,
    mock_owlet_entry: MockConfigEntry,
) -> None:
    """Test that the reauth flow."""

    mock_owlet_entry.add_to_hass(hass)

    result = await mock_owlet_entry.start_reauth_flow(hass)
    mock_owlet_api.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == error


async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_owlet_api: AsyncMock,
    mock_owlet_entry: MockConfigEntry,
) -> None:
    """Testing reconfgure flow."""
    mock_owlet_entry.add_to_hass(hass)

    result = await mock_owlet_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    mock_owlet_api.authenticate.return_value = REAUTH_RETURN
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_password"},
    )

    assert result2["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    assert result2["reason"] == "reconfigure_successful"
    assert mock_owlet_entry.data[CONF_API_TOKEN] == REAUTH_RETURN[CONF_API_TOKEN]


@pytest.mark.parametrize(
    ("exception", "error"),
    [
        (OwletDevicesError, {"base": "no_devices"}),
        (OwletCredentialsError, {"base": "invalid_credentials"}),
        (Exception, {"base": "unknown"}),
    ],
)
async def test_reconfigure_flow_errors(
    hass: HomeAssistant,
    exception: Exception,
    error: dict[str, str],
    mock_owlet_api: AsyncMock,
    mock_owlet_entry: MockConfigEntry,
) -> None:
    """Test that the reauth flow."""

    mock_owlet_entry.add_to_hass(hass)

    result = await mock_owlet_entry.start_reconfigure_flow(hass)
    mock_owlet_api.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: PASSWORD},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == error
