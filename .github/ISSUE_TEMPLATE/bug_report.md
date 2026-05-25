---
name: Bug report
about: Create a report to help us improve
title: "[BUG] "
labels: bug
assignees: ''
---

## Describe the bug
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

## Expected behavior
A clear and concise description of what you expected to happen.

## Logs
Please paste relevant debug logs here. Enable debug logging first:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.icloud_shared_album: debug
```

```
Paste logs here
```

## Environment

| Item | Version |
|------|---------|
| Home Assistant | <!-- e.g. 2025.5.0 --> |
| Integration version | <!-- e.g. 1.0.0 --> |
| HACS version | <!-- e.g. 2.0.0 --> |

## iCloud album URL (remove token if sensitive)
`https://www.icloud.com/sharedalbum/#...`

## Additional context
Add any other context about the problem here.
