"""iCloud Shared Album integration for Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CARD_FILENAME, CARD_URL, CARD_VERSION, DOMAIN
from .coordinator import ICloudAlbumCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera"]

FRONTEND_REGISTERED = f"{DOMAIN}_frontend_registered"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card and load it on every dashboard."""
    if hass.data.get(FRONTEND_REGISTERED):
        return
    hass.data[FRONTEND_REGISTERED] = True

    card_path = Path(__file__).parent / "frontend" / CARD_FILENAME
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=CARD_URL,
                path=str(card_path),
                cache_headers=False,
            )
        ]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}")
    _LOGGER.debug("Registered Lovelace card at %s", CARD_URL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up iCloud Shared Album from a config entry."""
    try:
        await _async_register_frontend(hass)
    except Exception:  # noqa: BLE001 — the card is optional, the camera is not
        _LOGGER.warning(
            "Could not register the iCloud Slideshow Lovelace card; "
            "the camera entity will still work",
            exc_info=True,
        )

    coordinator = ICloudAlbumCoordinator(hass, entry)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        raise ConfigEntryNotReady(
            f"Could not connect to iCloud album: {exc}"
        ) from exc

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when options change so the new scan interval is applied
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options updates by reloading the entry."""
    _LOGGER.debug("Options updated for %s — reloading entry", entry.title)
    await hass.config_entries.async_reload(entry.entry_id)
