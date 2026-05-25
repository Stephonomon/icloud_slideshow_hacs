# iCloud Shared Album — Home Assistant Integration

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/release/Stephonomon/icloud_slideshow_hacs.svg)](https://github.com/Stephonomon/icloud_slideshow_hacs/releases)
[![License](https://img.shields.io/github/license/Stephonomon/icloud_slideshow_hacs.svg)](LICENSE)

Turn any **public iCloud Shared Album** into a Home Assistant camera entity that automatically rotates through your photos as a slideshow — no Apple account, no YAML, no shell commands required.

---

## ✨ Features

- 📷 Exposes a **camera entity** that serves album photos directly to Lovelace
- 🔀 **Random** or **sequential** photo rotation
- ⚙️ **Fully UI-configured** via the Home Assistant integrations panel
- 🔄 Adjustable rotation interval (10 s → 24 h)
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

Once configured, add a camera card to any dashboard:

```yaml
type: picture-entity
entity: camera.icloud_shared_album
show_name: false
show_state: false
```

Or use the visual editor: **Add Card → Picture Entity → choose your camera**.

For a full-bleed slideshow look, combine with a **Vertical Stack** or use the **Picture Glance** card.

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
