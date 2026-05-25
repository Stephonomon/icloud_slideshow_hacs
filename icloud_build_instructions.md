Home Assistant HACS Integration Specification

iCloud Shared Album Slideshow Integration

Goal

Create a Home Assistant custom integration installable through HACS that:

* Connects to a public iCloud Shared Album
* Fetches album contents directly from Apple’s undocumented shared album APIs
* Displays only images (not videos)
* Exposes a Home Assistant camera entity
* Randomly rotates photos on a configurable interval
* Supports configuration through the Home Assistant UI (config flow)
* Requires no Apple authentication
* Does not rely on shell commands, YAML automations, or local helper entities

⸻

Existing Discovery / Reverse Engineering

The following has already been confirmed working.

Shared Album Token

Example album (use your own public shared album URL):

https://www.icloud.com/sharedalbum/#YourAlbumTokenHere

Album token (the part after the # symbol in your URL):

YourAlbumTokenHere

iCloud Shared Album API

Base host:

p101-sharedstreams.icloud.com

Fetch Album Contents

POST request:

POST https://p101-sharedstreams.icloud.com/{TOKEN}/sharedstreams/webstream

Payload:

{
  "streamCtag": null
}

Returns:

* all photos
* all videos
* derivatives
* metadata

⸻

Fetch Signed Asset URLs

POST request:

POST https://p101-sharedstreams.icloud.com/{TOKEN}/sharedstreams/webasseturls

Payload:

{
  "photoGuids": ["GUID_HERE"]
}

Returns:

* signed CDN URLs
* temporary asset access URLs

⸻

Important API Notes

Image vs Video Detection

Videos include:

"mediaAssetType": "video"

Images do NOT contain this field.

Filter logic:

if item.get("mediaAssetType") != "video"

⸻

CDN URLs Expire

Returned URLs are signed and expire roughly every 24 hours.

The integration must:

* periodically fetch fresh asset URLs
* never permanently cache signed URLs

⸻

Redirect Handling

Apple sometimes returns:

HTTP 330

or:

{
  "X-Apple-MMe-Host": "pXXX-sharedstreams.icloud.com"
}

The client must:

* detect redirects
* switch hosts dynamically

⸻

Desired Integration Architecture

Integration Name

icloud_shared_album

⸻

Required Features

1. Config Flow

UI setup through Home Assistant.

User inputs:

Field	Type
Shared Album URL or Token	text
Refresh interval	integer
Randomization mode	optional
Image quality	optional

Example (user pastes their own public album URL):

https://www.icloud.com/sharedalbum/#YourAlbumTokenHere

The integration should automatically extract:

YourAlbumTokenHere

⸻

2. Camera Entity

Expose:

camera.icloud_shared_album

The camera entity should:

* always return a valid image
* update on configured interval
* serve image bytes directly
* not rely on /config/www
* not rely on local_file camera integration

Preferred implementation:

* subclass Camera
* implement async_camera_image()

⸻

3. DataUpdateCoordinator

Use Home Assistant’s DataUpdateCoordinator.

Responsibilities:

* refresh image on interval
* maintain album cache
* maintain list of image GUIDs
* fetch fresh signed URL when rotating image

Avoid:

* downloading the entire album every minute

Preferred strategy:

* fetch album metadata once every few hours
* refresh individual image URLs on demand

⸻

4. Random Photo Selection

Requirements:

* image-only
* no videos
* avoid immediate repeats if possible

Optional:

* sequential slideshow mode
* shuffle mode

⸻

5. Options Flow

User should be able to change:

* refresh interval
* image quality
* slideshow mode

without deleting the integration.

⸻

Home Assistant Requirements

Minimum HA Version

Target modern HA architecture.

Recommended:

2025.1+

⸻

Async Requirements

Use:

* aiohttp
* async methods
* async coordinators

Avoid:

* blocking urllib
* synchronous requests

⸻

Suggested Internal Structure

custom_components/
└── icloud_shared_album/
    ├── __init__.py
    ├── manifest.json
    ├── const.py
    ├── config_flow.py
    ├── options_flow.py
    ├── coordinator.py
    ├── camera.py
    ├── api.py
    ├── strings.json
    ├── translations/
    │   └── en.json
    └── icons.json

⸻

Suggested Responsibilities

api.py

Handles:

* Apple API requests
* redirects
* asset fetching
* signed URL generation
* image filtering

Should expose methods like:

async_get_album()
async_get_random_image_url()
async_download_image()

⸻

coordinator.py

Handles:

* timed refreshes
* caching
* current image state

⸻

camera.py

Implements:

* camera entity
* image serving
* entity updates

⸻

Manifest Requirements

manifest.json

{
  "domain": "icloud_shared_album",
  "name": "iCloud Shared Album",
  "version": "0.1.0",
  "documentation": "https://github.com/YOURNAME/icloud_shared_album",
  "issue_tracker": "https://github.com/YOURNAME/icloud_shared_album/issues",
  "codeowners": ["@YOURNAME"],
  "config_flow": true,
  "iot_class": "cloud_polling",
  "requirements": []
}

⸻

HACS Requirements

Repository Structure

repo-root/
├── hacs.json
├── README.md
└── custom_components/

⸻

hacs.json

{
  "name": "iCloud Shared Album",
  "content_in_root": false,
  "render_readme": true
}

⸻

Desired Installation Flow

User should be able to:

HACS
→ Custom repositories
→ Add GitHub repo
→ Install integration
→ Restart HA
→ Add Integration
→ Paste iCloud shared album URL
→ Done

No YAML required.

⸻

Desired Dashboard Usage

Simple Lovelace card:

type: picture-entity
entity: camera.icloud_shared_album
show_name: false
show_state: false

⸻

Important Design Constraints

Do NOT Use

Avoid:

* shell_command
* command_line sensors
* local_file camera
* filesystem image writes
* YAML setup
* polling entire album every refresh

⸻

Performance Considerations

Some albums may contain:

* thousands of photos
* videos intermixed

Requirements:

* cache album metadata
* avoid excessive API calls
* avoid downloading full-resolution images unnecessarily

⸻

Nice-to-Have Features

Future Features

Possible future enhancements:

Multiple albums

Support multiple config entries.

⸻

Album metadata sensor

Expose:

* photo count
* album title
* last updated

⸻

Favorite images

Allow favorites filtering.

⸻

Album image prefetching

Pre-cache next N images.

⸻

Transition effects

Frontend-only slideshow transitions.

⸻

Existing Working Prototype

A working standalone Python proof-of-concept already exists that:

* fetches album metadata
* filters images
* fetches signed URLs
* downloads images successfully

This prototype currently uses:

* synchronous urllib
* filesystem writes
* shell commands

The integration should modernize this into native HA async architecture.

⸻

Deliverables

Required

* Complete Home Assistant custom integration
* HACS-compatible repo
* README with installation instructions
* Config flow
* Camera entity
* Interval-based slideshow updates
* Public GitHub repository

⸻

Recommended Development Flow

1. Build locally in /config/custom_components
2. Test in Home Assistant
3. Push to GitHub
4. Add HACS support
5. Validate through HACS
6. Release v0.1.0

⸻

Example Public Album

Use your own public iCloud Shared Album URL for testing. The format looks like:

https://www.icloud.com/sharedalbum/#YourAlbumTokenHere

(Enable "Public Website" on the album in the Photos app to get this link.)

⸻

Success Criteria

The final integration should allow a Home Assistant user to:

1. Install through HACS
2. Paste a public iCloud Shared Album URL
3. Add a camera card to Lovelace
4. Automatically rotate random album images
5. Configure refresh interval entirely from UI
6. Never touch YAML or shell commands