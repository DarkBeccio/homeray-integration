# Homeray integration

**The checks your dashboard cannot do on its own.** A small, free Home Assistant integration that works alongside the [Homeray cards](https://github.com/DarkBeccio/homeray-cards). It reads only Home Assistant's own data: it sends nothing to your devices and nothing to the internet.

[![hacs](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![release](https://img.shields.io/github/v/release/DarkBeccio/homeray-integration)](https://github.com/DarkBeccio/homeray-integration/releases)
[![license](https://img.shields.io/github/license/DarkBeccio/homeray-integration)](LICENSE)

🇮🇹 [Leggi in italiano](README.it.md)

## What it adds

| | What it does |
| --- | --- |
| **Silent devices** | Finds devices that still look available but have sent nothing for hours. This is how a battery device usually dies: it keeps its last value (often "80 %") and is never marked unavailable, so the built-in Maintenance dashboard does not see it. |
| **Every battery** | Percentage sensors, binary "low" sensors and low/medium/high sensors, one row per device. A battery sensor that stopped reporting while the rest of the device works is listed too. Phones and home storage batteries are left out, because a low level is normal for them. |
| **Your home network** | Finds your router, switches, access points, powerline adapters and servers among your devices, with the floor and room you gave them in Home Assistant and the Ping sensor that watches them. The Homeray Pro map uses this to draw your network with no configuration. |

### Compared with the built-in Maintenance dashboard

| | Maintenance dashboard | Homeray |
| --- | --- | --- |
| Unavailable devices and low batteries | ✓ | ✓ |
| Devices that died without becoming unavailable | | ✓ |
| Low/medium/high battery sensors | | ✓ |
| Ignore phones and home storage batteries | | ✓ |
| Ignore single devices (label) | | ✓ |
| Sensors to use in automations and notifications | | ✓ |

## Installation

**Home Assistant 2026.11 or newer (Marketplace):**

1. Settings → **Marketplace** → **Add from link** (top right) → `https://github.com/DarkBeccio/homeray-integration` → Add.
2. Find **Homeray** (type Integration) → **Install**. The setup opens by itself; a restart may be asked after updates.

**Older versions with HACS:**

1. HACS → three dots (top right) → **Custom repositories** → `https://github.com/DarkBeccio/homeray-integration`, type **Integration**.
2. Search for **Homeray** in HACS, **Download**, then restart Home Assistant.
3. Settings → Devices & services → **Add integration** → **Homeray**.

Requires Home Assistant 2026.1 or newer.

## Options

Settings → Devices & services → Homeray → **Configure**.

| Option | Default | What it does |
| --- | --- | --- |
| Silent after (hours) | 24 | How long a device may send nothing before it is listed as silent |
| Devices to watch | Battery-powered only | Or all devices with sensors |
| Low battery below (%) | 20 | Threshold for percentage sensors |
| Ignore rechargeable batteries | On | Leaves out phones and devices with a charging or storage sensor |
| Label of devices to ignore | `fuori_monitoraggio` | The same label used by the Homeray issues card |

A restart starts the clock again: Home Assistant does not keep the time of the last report across restarts, so right after a restart nothing can be silent yet. The `ready` attribute tells you when the check is active.

## Sensors

| Entity | State | Attributes |
| --- | --- | --- |
| `sensor.homeray_silent_devices` | Number of silent devices | `devices` (name, device_id, hours), `silent_after_hours`, `ready` |
| `sensor.homeray_low_batteries` | Number of low batteries | `batteries` (name, entity_id, kind, level) |

Example notification:

```yaml
triggers:
  - trigger: numeric_state
    entity_id: sensor.homeray_silent_devices
    above: 0
actions:
  - action: notify.notify
    data:
      message: >
        Silent: {{ state_attr('sensor.homeray_silent_devices', 'devices') | map(attribute='name') | join(', ') }}
```

## Network map

For devices Homeray does not recognise, or to correct it, add a label to the device: `homeray_router`, `homeray_switch`, `homeray_ap`, `homeray_powerline`, `homeray_powerline_wifi`, `homeray_server` or `homeray_alarm`. `homeray_hide` leaves a device out. Floors and rooms come from Home Assistant (Settings → Areas, labels & zones).

Recognised today: FRITZ!, UniFi, TP-Link Omada, devolo, ASUS, Netgear, MikroTik, OpenWrt, Keenetic, Huawei LTE, Vodafone Station, Freebox, SFR Box, UPnP routers, Synology, QNAP, TrueNAS, Proxmox and the Home Assistant host.

## For card developers

Two WebSocket commands, read-only and for administrators only: `homeray/status` (silent devices, batteries, options) and `homeray/network` (floors and network devices). Homeray is meant for whoever runs the smart home; other users get an `unauthorized` error.

## Support

Bugs and ideas: [GitHub issues](https://github.com/DarkBeccio/homeray-integration/issues) or support@homeray.app. If Homeray helps you, you can [buy me a coffee](https://paypal.me/AndreaGuarducci1992).

MIT License © 2026 DarkBeccio
