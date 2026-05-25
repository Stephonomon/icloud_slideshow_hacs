"""Config flow for iCloud Shared Album integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ICloudSharedAlbumAPI, extract_token
from .const import (
    CONF_ALBUM_URL,
    CONF_IMAGE_QUALITY,
    CONF_SCAN_INTERVAL,
    CONF_SLIDESHOW_MODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_RANDOM,
    MODE_SEQUENTIAL,
    QUALITY_MEDIUM,
    QUALITY_ORIGINAL,
    QUALITY_SMALL,
)

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

_SLIDESHOW_OPTIONS = [
    {"value": MODE_RANDOM, "label": "Random"},
    {"value": MODE_SEQUENTIAL, "label": "Sequential"},
]

_QUALITY_OPTIONS = [
    {"value": QUALITY_ORIGINAL, "label": "Original (largest)"},
    {"value": QUALITY_MEDIUM, "label": "Medium"},
    {"value": QUALITY_SMALL, "label": "Small (fastest)"},
]


def _user_schema(
    defaults: dict | None = None,
    include_url: bool = True,
) -> vol.Schema:
    defaults = defaults or {}
    fields: dict[vol.Marker, Any] = {}

    if include_url:
        fields[vol.Required(CONF_ALBUM_URL)] = TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        )

    fields[vol.Optional(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))] = (
        NumberSelector(
            NumberSelectorConfig(
                min=10,
                max=86400,
                step=1,
                unit_of_measurement="seconds",
                mode=NumberSelectorMode.BOX,
            )
        )
    )
    fields[vol.Optional(CONF_SLIDESHOW_MODE, default=defaults.get(CONF_SLIDESHOW_MODE, MODE_RANDOM))] = (
        SelectSelector(
            SelectSelectorConfig(
                options=_SLIDESHOW_OPTIONS,
                mode=SelectSelectorMode.LIST,
            )
        )
    )
    fields[vol.Optional(CONF_IMAGE_QUALITY, default=defaults.get(CONF_IMAGE_QUALITY, QUALITY_ORIGINAL))] = (
        SelectSelector(
            SelectSelectorConfig(
                options=_QUALITY_OPTIONS,
                mode=SelectSelectorMode.LIST,
            )
        )
    )
    return vol.Schema(fields)


# ---------------------------------------------------------------------------
# Config flow
# ---------------------------------------------------------------------------


class ICloudSharedAlbumConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle the initial setup of an iCloud Shared Album integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_url = user_input.get(CONF_ALBUM_URL, "").strip()
            token = extract_token(raw_url)

            if not token:
                errors[CONF_ALBUM_URL] = "invalid_url"
            else:
                # Check for duplicate
                await self.async_set_unique_id(token)
                self._abort_if_unique_id_configured()

                # Validate by fetching the album
                session = async_get_clientsession(self.hass)
                api = ICloudSharedAlbumAPI(session, token)
                try:
                    photos = await api.async_get_album()
                except Exception:  # noqa: BLE001
                    errors["base"] = "cannot_connect"
                else:
                    if not photos:
                        errors[CONF_ALBUM_URL] = "no_photos"
                    else:
                        scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
                        return self.async_create_entry(
                            title=f"iCloud Album ({token[:8]}…)",
                            data={
                                "token": token,
                                CONF_SCAN_INTERVAL: scan_interval,
                                CONF_SLIDESHOW_MODE: user_input.get(CONF_SLIDESHOW_MODE, MODE_RANDOM),
                                CONF_IMAGE_QUALITY: user_input.get(CONF_IMAGE_QUALITY, QUALITY_ORIGINAL),
                            },
                        )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(),
            errors=errors,
            description_placeholders={
                "readme_url": "https://github.com/Stephonomon/icloud_slideshow_hacs#readme"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ICloudSharedAlbumOptionsFlow:
        """Return the options flow handler."""
        return ICloudSharedAlbumOptionsFlow(config_entry)


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


class ICloudSharedAlbumOptionsFlow(config_entries.OptionsFlow):
    """Allow changing interval, mode, and quality without re-adding the entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the options form."""
        if user_input is not None:
            user_input[CONF_SCAN_INTERVAL] = int(user_input[CONF_SCAN_INTERVAL])
            return self.async_create_entry(title="", data=user_input)

        current = {
            CONF_SCAN_INTERVAL: self._config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
            CONF_SLIDESHOW_MODE: self._config_entry.options.get(
                CONF_SLIDESHOW_MODE,
                self._config_entry.data.get(CONF_SLIDESHOW_MODE, MODE_RANDOM),
            ),
            CONF_IMAGE_QUALITY: self._config_entry.options.get(
                CONF_IMAGE_QUALITY,
                self._config_entry.data.get(CONF_IMAGE_QUALITY, QUALITY_ORIGINAL),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=_user_schema(defaults=current, include_url=False),
        )
