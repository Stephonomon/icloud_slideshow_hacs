"""DataUpdateCoordinator for iCloud Shared Album."""
from __future__ import annotations

import logging
import random
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ICloudSharedAlbumAPI
from .const import (
    CONF_IMAGE_QUALITY,
    CONF_SCAN_INTERVAL,
    CONF_SLIDESHOW_MODE,
    DEFAULT_ALBUM_REFRESH_HOURS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MODE_RANDOM,
    MODE_SEQUENTIAL,
    QUALITY_ORIGINAL,
)

_LOGGER = logging.getLogger(__name__)


class ICloudAlbumCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages periodic image rotation from an iCloud shared album."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self._api = ICloudSharedAlbumAPI(
            async_get_clientsession(hass),
            entry.data["token"],
        )

        scan_interval = self._get_option(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

        # Album metadata cache
        self._photos: list[dict[str, Any]] = []
        self._last_album_refresh: float | None = None

        # Slideshow state
        self._seq_index: int = 0
        self._last_guid: str | None = None

        # Current frame
        self.current_image: bytes | None = None

    # ------------------------------------------------------------------
    # DataUpdateCoordinator interface
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Rotate to the next image and return metadata."""
        try:
            await self._maybe_refresh_album()

            if not self._photos:
                raise UpdateFailed("iCloud album contains no images")

            photo = self._next_photo()
            quality = self._get_option(CONF_IMAGE_QUALITY, QUALITY_ORIGINAL)

            cdn_url = await self._api.async_get_asset_url(photo, quality)
            if not cdn_url:
                raise UpdateFailed("Could not obtain a signed CDN URL for photo")

            image_bytes = await self._api.async_download_image(cdn_url)
            if not image_bytes:
                raise UpdateFailed("Image download returned no data")

            self.current_image = image_bytes
            self._last_guid = photo.get("photoGuid")

            return {
                "photo_count": len(self._photos),
                "current_guid": self._last_guid,
            }

        except UpdateFailed:
            raise
        except Exception as exc:
            raise UpdateFailed(f"Unexpected error fetching iCloud image: {exc}") from exc

    # ------------------------------------------------------------------
    # Options helpers
    # ------------------------------------------------------------------

    def _get_option(self, key: str, default: Any) -> Any:
        """Return the current option value, preferring options over data."""
        return self._entry.options.get(key, self._entry.data.get(key, default))

    def update_scan_interval(self) -> None:
        """Update the polling interval from current options (call after reload)."""
        seconds = self._get_option(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.update_interval = timedelta(seconds=seconds)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _maybe_refresh_album(self) -> None:
        """Re-fetch album metadata when the cache is stale."""
        refresh_seconds = DEFAULT_ALBUM_REFRESH_HOURS * 3600
        now = time.monotonic()
        if (
            self._last_album_refresh is None
            or (now - self._last_album_refresh) >= refresh_seconds
        ):
            _LOGGER.debug("Refreshing iCloud album metadata for %s", self._entry.title)
            self._photos = await self._api.async_get_album()
            self._last_album_refresh = now
            self._seq_index = 0
            _LOGGER.info(
                "iCloud album refreshed: %d images available", len(self._photos)
            )

    def _next_photo(self) -> dict[str, Any]:
        """Pick the next photo according to the configured slideshow mode."""
        mode = self._get_option(CONF_SLIDESHOW_MODE, MODE_RANDOM)

        if mode == MODE_SEQUENTIAL:
            photo = self._photos[self._seq_index % len(self._photos)]
            self._seq_index += 1
            return photo

        # Random mode — avoid immediate repeat when there are multiple photos
        if len(self._photos) > 1 and self._last_guid:
            candidates = [
                p for p in self._photos if p.get("photoGuid") != self._last_guid
            ]
            if candidates:
                return random.choice(candidates)

        return random.choice(self._photos)
