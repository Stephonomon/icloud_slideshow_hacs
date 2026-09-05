"""Camera platform for iCloud Shared Album."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CURRENT_GUID,
    ATTR_LAST_CHANGE,
    ATTR_NEXT_CHANGE,
    ATTR_PHOTO_COUNT,
    ATTR_ROTATION_INTERVAL,
    DOMAIN,
)
from .coordinator import ICloudAlbumCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the iCloud Shared Album camera from a config entry."""
    coordinator: ICloudAlbumCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ICloudAlbumCamera(coordinator, entry)])


class ICloudAlbumCamera(CoordinatorEntity[ICloudAlbumCoordinator], Camera):
    """Camera entity that serves rotating images from an iCloud shared album."""

    _attr_has_entity_name = True
    _attr_name = None  # Entity name = device name
    _attr_is_streaming = False
    _attr_icon = "mdi:image-multiple"

    def __init__(
        self,
        coordinator: ICloudAlbumCoordinator,
        entry: ConfigEntry,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)

        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Apple",
            model="iCloud Shared Album",
            configuration_url=f"https://www.icloud.com/sharedalbum/#{entry.data.get('token', '')}",
        )

    # ------------------------------------------------------------------
    # Camera interface
    # ------------------------------------------------------------------

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Return the current cached image bytes."""
        return self.coordinator.current_image

    @property
    def frame_interval(self) -> float:
        """Poll interval for the MJPEG still stream.

        The stream endpoint is what the more-info dialog renders, so keep it
        short enough that a rotation shows up promptly there too.
        """
        return 1.0

    @property
    def entity_picture(self) -> str | None:
        """Return the proxy URL with a per-rotation cache buster.

        Without this the URL is identical for every photo, so any consumer that
        renders it as a plain <img> (a fullscreen/expanded view, for example)
        keeps showing the first frame the browser cached.
        """
        picture = super().entity_picture
        if not picture:
            return picture
        separator = "&" if "?" in picture else "?"
        return f"{picture}{separator}v={self.coordinator.image_revision}"

    # ------------------------------------------------------------------
    # Extra state attributes
    # ------------------------------------------------------------------

    @property
    def extra_state_attributes(self) -> dict:
        """Expose photo count, current GUID, and rotation timing."""
        data = self.coordinator.data or {}
        interval = self.coordinator.scan_interval
        last_change = self.coordinator.last_change

        return {
            ATTR_PHOTO_COUNT: data.get(ATTR_PHOTO_COUNT),
            ATTR_CURRENT_GUID: data.get(ATTR_CURRENT_GUID),
            ATTR_ROTATION_INTERVAL: interval,
            ATTR_LAST_CHANGE: last_change.isoformat() if last_change else None,
            ATTR_NEXT_CHANGE: (
                (last_change + timedelta(seconds=interval)).isoformat()
                if last_change
                else None
            ),
        }
