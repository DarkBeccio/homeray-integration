# Changelog

## 1.0.2 - 2026-11-09

- The WebSocket commands `homeray/status` and `homeray/network` now answer only administrators: they return device names, areas and network addresses, which guest or kiosk accounts should not read. The Homeray cards keep working for other users without the integration's extra panels.

## 1.0.1 - 2026-11-09

- Homeray icon inside the integration (`brand/` folder), shown by Home Assistant 2026.3 and newer.

## 1.0.0 - 2026-11-09

- First release: silent devices, every battery, home network discovery for the Homeray Pro map, two sensors, options in English and Italian.
- Install from the Marketplace of Home Assistant 2026.11 or from HACS as a custom repository.
