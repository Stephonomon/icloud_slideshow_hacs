"""Constants for iCloud Shared Album integration."""

DOMAIN = "icloud_shared_album"

# Configuration keys
CONF_NAME = "name"
CONF_ALBUM_URL = "album_url"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SLIDESHOW_MODE = "slideshow_mode"
CONF_IMAGE_QUALITY = "image_quality"

# Slideshow modes
MODE_RANDOM = "random"
MODE_SEQUENTIAL = "sequential"

# Image quality options
QUALITY_ORIGINAL = "original"
QUALITY_MEDIUM = "medium"
QUALITY_SMALL = "small"

# Defaults
DEFAULT_SCAN_INTERVAL = 15          # seconds between photo rotations
MIN_SCAN_INTERVAL = 5               # fastest rotation the config flow allows
MAX_SCAN_INTERVAL = 86400           # slowest rotation the config flow allows
DEFAULT_ALBUM_REFRESH_HOURS = 1     # hours between full album metadata refreshes

# Extra state attributes
ATTR_PHOTO_COUNT = "photo_count"
ATTR_CURRENT_GUID = "current_guid"
ATTR_ROTATION_INTERVAL = "rotation_interval"
ATTR_LAST_CHANGE = "last_change"
ATTR_NEXT_CHANGE = "next_change"

# Bundled Lovelace card
CARD_VERSION = "1.2.0"
CARD_FILENAME = "icloud-slideshow-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILENAME}"

# iCloud API
ICLOUD_BASE_HOST = "p101-sharedstreams.icloud.com"
ICLOUD_WEBSTREAM_PATH = "sharedstreams/webstream"
ICLOUD_WEBASSETURLS_PATH = "sharedstreams/webasseturls"
