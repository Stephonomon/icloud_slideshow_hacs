# Contributing to iCloud Shared Album

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

1. **Fork** this repository and clone your fork.
2. Copy `custom_components/icloud_shared_album` into your Home Assistant `config/custom_components/` directory (or use a dev container).
3. Restart Home Assistant and add the integration via **Settings → Devices & Services**.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) Python style.
- Use type hints throughout (`from __future__ import annotations`).
- Use `async`/`await` — no blocking calls.
- Keep log messages meaningful and use the appropriate level (`debug`, `info`, `warning`, `error`).

## Submitting a Pull Request

1. Create a branch: `git checkout -b feature/my-feature`
2. Make your changes.
3. Run a quick sanity check: confirm the integration loads cleanly in HA and the camera entity works.
4. Open a PR against `main` with a clear description of what changed and why.

## Reporting Bugs

Please use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include debug logs.

## API Notes

Apple's iCloud shared album API is undocumented and may change. Key endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /{token}/sharedstreams/webstream` | Fetch album metadata and photo list |
| `POST /{token}/sharedstreams/webasseturls` | Get signed CDN URLs for specific photos |

The host can redirect via HTTP 330 or the `X-Apple-MMe-Host` header — always follow these redirects.
