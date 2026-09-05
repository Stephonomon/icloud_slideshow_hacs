# iCloud Shared Album — Home Assistant Integration

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/release/Stephonomon/icloud_slideshow_hacs.svg)](https://github.com/Stephonomon/icloud_slideshow_hacs/releases)
[![License](https://img.shields.io/github/license/Stephonomon/icloud_slideshow_hacs.svg)](LICENSE)

Turn any **public iCloud Shared Album** into a Home Assistant camera entity that automatically rotates through your photos as a slideshow — no Apple account, no YAML, no shell commands required.

---

## ✨ Features

- 📷 Exposes a **camera entity** that serves album photos directly to Lovelace
- 🎞️ Bundled **Lovelace card** with a crossfade, a rotation **progress bar**, and a fullscreen view that keeps rotating
- 🔀 **Random** or **sequential** photo rotation
- ⚙️ **Fully UI-configured** via the Home Assistant integrations panel
- 🔄 Adjustable rotation interval (5 s → 24 h, default 15 s)
- 🖼️ Selectable image quality (Original / Medium / Small)
- 🚫 Automatically skips videos — images only
- 💾 Caches album metadata to minimize API calls
- 🔒 No Apple sign-in required — works with any public shared album URL

---

## 📋 Requirements

| Item | Minimum |
|------|---------|
| Home Assistant | 2025.1.0 |
| HACS | Any current release |
| iCloud Shared Album | Must be set to **public** ("Anyone with the link") |

---

## 🚀 Installation via HACS (recommended)

1. Open **HACS** in your Home Assistant sidebar.
2. Click the **⋮ menu** (top-right) → **Custom repositories**.
3. Add the URL `https://github.com/Stephonomon/icloud_slideshow_hacs` and set category to **Integration**.
4. Search for **iCloud Shared Album** and click **Download**.
5. **Restart Home Assistant**.

---

## 🔧 Manual Installation

1. Download the [latest release](https://github.com/Stephonomon/icloud_slideshow_hacs/releases/latest).
2. Copy the `custom_components/icloud_shared_album` folder into your HA `config/custom_components/` directory.
3. **Restart Home Assistant**.

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **iCloud Shared Album**.
3. Paste **your own** public iCloud Shared Album URL. It will look like this:
   ```
   https://www.icloud.com/sharedalbum/#YourAlbumTokenHere
   ```
   > ⚠️ **You must use your own album link.** See the section below for how to find it.
4. Set your preferred options and click **Submit**.

### How to get your iCloud Shared Album URL

1. Open the **Photos** app on your iPhone, iPad, or Mac.
2. Navigate to **Shared Albums** and open the album you want.
3. Tap or click **…** → **Shared Album Settings** (or use the sharing sheet).
4. Enable **Public Website** (this makes the album accessible without an Apple ID).
5. Copy the **Public Website** link — it ends with a `#` followed by your album token.

> **Note:** The album must have **Public Website** enabled. Private albums are not supported.

---

## 📐 Lovelace Dashboard

### Slideshow card (recommended)

The integration ships its own card and registers it automatically — there is
nothing to add under **Settings → Dashboards → Resources**. Add it from the
card picker (**Add Card → iCloud Slideshow**) or paste:

```yaml
type: custom:icloud-slideshow-card
entity: camera.icloud_shared_album
```

It crossfades between photos, draws a thin progress bar showing how long is
left before the next one, and tapping it goes fullscreen — where the photos
keep rotating.

| Option | Default | Description |
|--------|---------|-------------|
| `entity` | *(required)* | The camera entity from this integration. |
| `fit` | `cover` | `cover` fills the card (crops); `contain` letterboxes. Fullscreen always uses `contain`. |
| `aspect_ratio` | `16:9` | Card shape, e.g. `4:3`, `1:1`, `21:9`. |
| `show_progress` | `true` | Show the rotation progress bar. |
| `progress_position` | `bottom` | `bottom` or `top`. |
| `progress_height` | `4` | Bar thickness in pixels. |
| `progress_color` | theme accent | Any CSS color. |
| `transition` | `700` | Crossfade duration in milliseconds. Set `0` for a hard cut. |
| `tap_action` | `fullscreen` | `fullscreen`, `more-info`, or `none`. |

A fuller example:

```yaml
type: custom:icloud-slideshow-card
entity: camera.icloud_shared_album
aspect_ratio: "4:3"
fit: contain
progress_height: 3
progress_color: rgba(255, 255, 255, 0.85)
transition: 1200
```

### Built-in cards

The standard cards still work if you prefer them:

```yaml
type: picture-entity
entity: camera.icloud_shared_album
show_name: false
show_state: false
```

### Entity attributes

The camera exposes the rotation schedule, so you can drive your own cards or
automations from it:

| Attribute | Description |
|-----------|-------------|
| `photo_count` | Number of images in the album. |
| `current_guid` | GUID of the photo on screen. |
| `rotation_interval` | Configured interval, in seconds. |
| `last_change` | ISO timestamp of the current photo's arrival. |
| `next_change` | ISO timestamp of the next rotation. |

---

## 🔄 Changing Settings

You can update the rotation interval, slideshow mode, or image quality at any time **without removing the integration**:

1. Go to **Settings → Devices & Services**.
2. Find **iCloud Shared Album** and click **Configure**.
3. Adjust your options and click **Submit**.

---

## 🏗️ How It Works

```
Home Assistant
    │
    ▼
ICloudAlbumCoordinator
    │  Polls on configured interval
    │
    ├─► ICloudSharedAlbumAPI.async_get_album()
    │       POST /sharedstreams/webstream  →  list of image GUIDs
    │       (cached for 1 hour — avoids hammering Apple's API)
    │
    ├─► Pick next image (random or sequential)
    │
    ├─► ICloudSharedAlbumAPI.async_get_asset_url()
    │       POST /sharedstreams/webasseturls  →  fresh signed CDN URL
    │
    ├─► ICloudSharedAlbumAPI.async_download_image()
    │       GET signed CDN URL  →  image bytes
    │
    └─► Camera entity serves bytes to Lovelace
```

Apple's CDN URLs expire (~24 hours), so fresh URLs are fetched on every rotation. Album metadata (photo list) is re-fetched once per hour to pick up new photos without hammering the API.

---

## 🐛 Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Unable to reach iCloud" during setup | Check the URL. Make sure **Public Website** is enabled on the album. |
| Camera shows a broken image | The album may be empty or Apple's API returned an error. Check logs. |
| Photos stop rotating | Verify your internet connection. Check HA logs for `icloud_shared_album`. |
| Only seeing one photo | There may be only one image in the album, or the album has only videos. |
| Card doesn't appear in the picker | Hard-refresh the browser (Ctrl/Cmd + Shift + R) so the newly registered card script loads. |
| Want to force a refresh | Reload the integration: **Settings → Devices & Services → ⋮ → Reload**. |

Enable debug logging for detailed output:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.icloud_shared_album: debug
```

---

## 🗺️ Roadmap

- [ ] Multiple albums (multiple config entries already supported — just add another)
- [ ] Album metadata sensor (photo count, album name, last refreshed)
- [ ] Service call to manually advance to the next photo
- [ ] Favorites-only mode
- [ ] Prefetch next image for seamless rotation
- [ ] Tap-to-pause and manual next/previous on the slideshow card

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!

1. Fork the repository.
2. Create a branch: `git checkout -b feature/my-feature`.
3. Make your changes and add tests if applicable.
4. Open a pull request describing what you changed and why.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📜 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## ⚠️ Disclaimer

This integration uses Apple's **undocumented** iCloud shared album API. It may break if Apple changes the API without notice. It is not affiliated with or endorsed by Apple Inc.
