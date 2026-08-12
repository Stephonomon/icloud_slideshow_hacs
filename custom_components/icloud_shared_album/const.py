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
DEFAULT_SCAN_INTERVAL = 30          # seconds between photo rotations
DEFAULT_ALBUM_REFRESH_HOURS = 1     # hours between full album metadata refreshes

# iCloud API
ICLOUD_BASE_HOST = "p101-sharedstreams.icloud.com"
ICLOUD_WEBSTREAM_PATH = "sharedstreams/webstream"
ICLOUD_WEBASSETURLS_PATH = "sharedstreams/webasseturls"
