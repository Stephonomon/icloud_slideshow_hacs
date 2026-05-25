"""iCloud Shared Album API client."""
from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp

from .const import (
    ICLOUD_BASE_HOST,
    ICLOUD_WEBSTREAM_PATH,
    ICLOUD_WEBASSETURLS_PATH,
    QUALITY_ORIGINAL,
    QUALITY_MEDIUM,
    QUALITY_SMALL,
)

_LOGGER = logging.getLogger(__name__)

# Regex to pull token from a full iCloud shared album URL
_TOKEN_RE = re.compile(r"#([A-Za-z0-9_-]+)$")


def extract_token(url_or_token: str) -> str | None:
    """Extract the album token from a URL or return raw token if valid."""
    url_or_token = url_or_token.strip()
    match = _TOKEN_RE.search(url_or_token)
    if match:
        return match.group(1)
    # Looks like a raw token (only word characters)
    if re.match(r"^[A-Za-z0-9_-]+$", url_or_token):
        return url_or_token
    return None


class ICloudSharedAlbumAPI:
    """Async client for Apple's undocumented iCloud shared album APIs."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._token = token
        self._host = ICLOUD_BASE_HOST

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def async_get_album(self) -> list[dict[str, Any]]:
        """Fetch the album's webstream and return only image items (no videos)."""
        url = self._webstream_url()
        data = await self._post(url, {"streamCtag": None})

        photos: list[dict] = data.get("photos", [])
        images = [p for p in photos if p.get("mediaAssetType") != "video"]
        _LOGGER.debug(
            "iCloud album %s: %d total items, %d images",
            self._token[:8],
            len(photos),
            len(images),
        )
        return images

    async def async_get_asset_url(
        self, photo: dict[str, Any], quality: str = QUALITY_ORIGINAL
    ) -> str | None:
        """Return a fresh signed CDN URL for the chosen photo and quality."""
        guid: str | None = photo.get("photoGuid")
        derivatives: dict = photo.get("derivatives", {})

        if not guid or not derivatives:
            _LOGGER.warning("Photo missing guid or derivatives: %s", photo)
            return None

        # Pick which derivative checksum we want
        checksum = self._pick_checksum(derivatives, quality)
        if not checksum:
            _LOGGER.warning("Could not determine checksum for quality %s", quality)
            return None

        url = self._webasseturls_url()
        data = await self._post(url, {"photoGuids": [guid]})

        return self._parse_asset_url(data, checksum)

    async def async_download_image(self, cdn_url: str) -> bytes | None:
        """Download raw image bytes from a CDN URL."""
        try:
            async with self._session.get(cdn_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    return await resp.read()
                _LOGGER.warning("Image download returned HTTP %s for %s", resp.status, cdn_url)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("Failed to download image from %s: %s", cdn_url, exc)
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _webstream_url(self) -> str:
        return f"https://{self._host}/{self._token}/{ICLOUD_WEBSTREAM_PATH}"

    def _webasseturls_url(self) -> str:
        return f"https://{self._host}/{self._token}/{ICLOUD_WEBASSETURLS_PATH}"

    async def _post(self, url: str, payload: dict) -> dict:
        """POST with Apple-specific redirect handling (HTTP 330 / X-Apple-MMe-Host)."""
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.icloud.com",
        }
        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                # Apple returns a non-standard 330 when we must change partitions
                if resp.status == 330:
                    body = await resp.json(content_type=None)
                    new_host = body.get("X-Apple-MMe-Host")
                    if new_host:
                        _LOGGER.debug("iCloud redirect: switching host to %s", new_host)
                        self._host = new_host
                        return await self._post(
                            url.replace(ICLOUD_BASE_HOST, new_host), payload
                        )

                # Some responses include the redirect as a header even on 200
                if apple_host := resp.headers.get("X-Apple-MMe-Host"):
                    _LOGGER.debug("iCloud host header: %s", apple_host)
                    self._host = apple_host

                resp.raise_for_status()
                return await resp.json(content_type=None)

        except aiohttp.ClientResponseError as exc:
            _LOGGER.error("iCloud API HTTP error %s for %s", exc.status, url)
            raise
        except Exception as exc:
            _LOGGER.error("iCloud API request failed for %s: %s", url, exc)
            raise

    @staticmethod
    def _pick_checksum(derivatives: dict, quality: str) -> str | None:
        """Choose a derivative checksum based on the requested quality."""
        items = [v for v in derivatives.values() if isinstance(v, dict)]
        if not items:
            return None

        # Sort ascending by file size; largest = original, smallest = small
        items_sorted = sorted(items, key=lambda d: d.get("fileSize", 0))

        if quality == QUALITY_SMALL:
            chosen = items_sorted[0]
        elif quality == QUALITY_MEDIUM:
            chosen = items_sorted[len(items_sorted) // 2]
        else:  # QUALITY_ORIGINAL or fallback
            chosen = items_sorted[-1]

        return chosen.get("checksum")

    @staticmethod
    def _parse_asset_url(data: dict, checksum: str) -> str | None:
        """Build the full CDN URL from a webasseturls response."""
        items: dict = data.get("items", {})
        locations: dict = data.get("locations", {})

        item = items.get(checksum)
        if not item:
            # Fall back to first item if exact checksum not found
            if items:
                item = next(iter(items.values()))
            else:
                _LOGGER.warning("webasseturls response contained no items")
                return None

        url_location: str | None = item.get("url_location")
        url_path: str | None = item.get("url_path")

        if not url_path:
            _LOGGER.warning("No url_path in webasseturls item: %s", item)
            return None

        if url_location and url_location in locations:
            loc = locations[url_location]
            scheme = loc.get("scheme", "https")
            hosts: list = loc.get("hosts", [url_location])
            host = hosts[0] if hosts else url_location
            return f"{scheme}://{host}{url_path}"

        # Minimal fallback — use url_path as-is if it looks absolute
        if url_path.startswith("http"):
            return url_path

        _LOGGER.warning("Cannot build CDN URL from item: %s", item)
        return None
