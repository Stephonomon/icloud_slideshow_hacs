"""Camera platform for iCloud Shared Album."""
from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
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

    # ------------------------------------------------------------------
    # Extra state attributes
    # ------------------------------------------------------------------

    @property
    def extra_state_attributes(self) -> dict:
        """Expose photo count and current GUID for diagnostics."""
        data = self.coordinator.data or {}
        return {
            "photo_count": data.get("photo_count"),
            "current_guid": data.get("current_guid"),
        }
