"""Finds the home network devices already known to Home Assistant, for the Homeray map.

Sources, all local: the device registry (models, links between devices, MAC addresses),
the floor and area registries (where each device is), router device trackers (IP addresses)
and Ping entries (status). Labels let the user add, retype or hide a device.
"""

from __future__ import annotations

import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    floor_registry as fr,
)
from homeassistant.util import slugify

from .const import LABEL_HIDE, LABEL_TYPES

# Integrations whose main device is the home router.
ROUTER_DOMAINS = {
    "fritz", "asuswrt", "netgear", "mikrotik", "luci", "ubus", "keenetic_ndms2",
    "huawei_lte", "vodafone_station", "freebox", "sfr_box", "bbox", "tplink_router",
    "upnp",
}
SERVER_DOMAINS = {"synology_dsm", "qnap", "qnap_qsw", "truenas", "proxmoxve", "unraid", "glances"}
PLC_DOMAINS = {"devolo_home_network"}
# Integrations that bring several network devices; the model tells what each one is.
MODEL_RULES: list[tuple[str, str]] = [
    (r"^(udm|udr|uxg|usg|ucg|udw|ux\b|uck)|dream ?(machine|router)|cloud gateway|gateway", "router"),
    (r"^(usw|us-|usl|usm|usp)|switch|^sg\d|^tl-sg|^gs\d", "switch"),
    (r"^(u6|u7|uap|ual|uac|uk|e7|eap)|access ?point|repeater|^deco|mesh", "ap"),
    (r"powerline|magic|dlan", "plc"),
    (r"^er\d|router|fritz!box|box\b", "router"),
]
TYPE_PRIORITY = {"router": 0, "switch": 1, "ap": 2, "plcwifi": 3, "plc": 3, "alarm": 4, "server": 5}


def _model_type(text: str) -> str | None:
    t = text.lower()
    for rx, kind in MODEL_RULES:
        if re.search(rx, t):
            return kind
    return None


def _macs(dev: dr.DeviceEntry) -> set[str]:
    return {v.lower() for k, v in dev.connections if k == dr.CONNECTION_NETWORK_MAC}


def _domains(hass: HomeAssistant, dev: dr.DeviceEntry) -> set[str]:
    out = set()
    for eid in dev.config_entries:
        entry = hass.config_entries.async_get_entry(eid)
        if entry:
            out.add(entry.domain)
    return out


def _classify(hass: HomeAssistant, dev: dr.DeviceEntry, ent_reg: er.EntityRegistry) -> str | None:
    for lab, kind in LABEL_TYPES.items():
        if lab in dev.labels:
            return kind
    domains = _domains(hass, dev)
    model = " ".join(x for x in (dev.model, dev.model_id, dev.name) if x)
    if domains & PLC_DOMAINS or re.search(r"powerline|dlan|magic", model.lower()):
        wifi = any(
            "wifi" in e.entity_id or "wlan" in e.entity_id or (e.translation_key or "").find("wifi") >= 0
            for e in er.async_entries_for_device(ent_reg, dev.id)
        )
        return "plcwifi" if wifi else "plc"
    if "hassio" in domains and (dev.model or "").lower().startswith("home assistant"):
        return "server"
    if domains & SERVER_DOMAINS:
        return "server"
    if domains & {"unifi", "tplink_omada", "tplink_deco", "omada", "deco"}:
        return _model_type(model)
    if domains & ROUTER_DOMAINS:
        return _model_type(model) if "fritz" in domains and "repeater" in model.lower() else "router"
    return None


def _ip_by_mac(hass: HomeAssistant) -> dict[str, str]:
    out = {}
    for st in hass.states.async_all("device_tracker"):
        mac, ip = st.attributes.get("mac"), st.attributes.get("ip")
        if mac and ip:
            out[str(mac).lower()] = str(ip)
    return out


def _ping_by_host(hass: HomeAssistant, ent_reg: er.EntityRegistry) -> dict[str, str]:
    out = {}
    for entry in hass.config_entries.async_entries("ping"):
        host = str(entry.options.get("host") or entry.data.get("host") or "").lower()
        if not host:
            continue
        for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
            if ent.domain == "binary_sensor" and not ent.disabled_by:
                out[host] = ent.entity_id
    return out


def discover(hass: HomeAssistant) -> dict[str, Any]:
    """The floors and network devices of the home, ready for the map card."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    area_reg = ar.async_get(hass)
    floors = sorted(
        fr.async_get(hass).async_list_floors(),
        key=lambda f: (f.level is None, -(f.level or 0), f.name.lower()),
    )
    floor_list = [{"id": f.floor_id, "name": f.name, "level": f.level} for f in floors]
    ips, pings = _ip_by_mac(hass), _ping_by_host(hass, ent_reg)

    found: list[tuple[dr.DeviceEntry, str]] = []
    seen_macs: set[str] = set()
    for dev in dev_reg.devices.values():
        if dev.disabled_by or LABEL_HIDE in dev.labels:
            continue
        kind = _classify(hass, dev, ent_reg)
        if not kind:
            continue
        found.append((dev, kind))
    # the same box can come from two integrations (e.g. FRITZ!Box and UPnP): keep one
    found.sort(key=lambda x: (TYPE_PRIORITY[x[1]], _domains(hass, x[0]) == {"upnp"}))
    unique: list[tuple[dr.DeviceEntry, str]] = []
    for dev, kind in found:
        macs = _macs(dev)
        if macs & seen_macs:
            continue
        if _domains(hass, dev) == {"upnp"} and kind == "router" and any(k == "router" for _, k in unique):
            continue
        seen_macs |= macs
        unique.append((dev, kind))

    ids: dict[str, str] = {}
    used: set[str] = set()
    for dev, _ in unique:
        base = slugify(dev.name_by_user or dev.name or dev.id) or "device"
        nid, i = base, 2
        while nid in used:
            nid, i = f"{base}_{i}", i + 1
        used.add(nid)
        ids[dev.id] = nid

    nodes: list[dict[str, Any]] = []
    for dev, kind in unique:
        area = area_reg.async_get_area(dev.area_id) if dev.area_id else None
        ip = next((ips[m] for m in _macs(dev) if m in ips), None)
        if not ip:
            for eid in dev.config_entries:
                entry = hass.config_entries.async_get_entry(eid)
                if entry and entry.domain in ROUTER_DOMAINS | SERVER_DOMAINS | PLC_DOMAINS and entry.data.get("host"):
                    ip = str(entry.data["host"])
                    break
        status = None
        for ent in er.async_entries_for_device(ent_reg, dev.id):
            if ent.domain == "binary_sensor" and not ent.disabled_by and (
                ent.original_device_class == "connectivity" or ent.device_class == "connectivity"
            ):
                status = ent.entity_id
                break
        name = dev.name_by_user or dev.name or ""
        for host in (ip, name.lower()):
            if host and host.lower() in pings:
                status = pings[host.lower()]
                break
        nodes.append(
            {
                "id": ids[dev.id],
                "device_id": dev.id,
                "type": kind,
                "name": name or ids[dev.id],
                "model": " ".join(x for x in (dev.manufacturer, dev.model) if x),
                "floor_id": area.floor_id if area else None,
                "area": area.name if area else None,
                "parent": ids.get(dev.via_device_id or ""),
                "ip": ip,
                "entity": status,
                "url": f"/config/devices/device/{dev.id}",
                "up": kind == "server" and "hassio" in _domains(hass, dev),
            }
        )

    # one router at the top; everything without a known upstream device hangs from it
    roots = [n for n in nodes if n["type"] == "router"]
    synthetic = False
    if roots:
        root = roots[0]
    else:
        root = {"id": "router", "device_id": None, "type": "router", "name": "Router", "model": "",
                "floor_id": None, "area": None, "parent": None, "ip": None, "entity": None, "url": None, "up": False}
        nodes.insert(0, root)
        synthetic = True
    root["parent"] = None
    for n in nodes:
        if n is not root and (not n["parent"] or n["parent"] == n["id"]):
            n["parent"] = root["id"]
    # break loops by sending the device straight to the router
    by = {n["id"]: n for n in nodes}
    for n in nodes:
        seen, cur = set(), n
        while cur["parent"]:
            if cur["id"] in seen:
                n["parent"] = root["id"]
                break
            seen.add(cur["id"])
            cur = by.get(cur["parent"]) or root
            if cur is root:
                break
    return {"floors": floor_list, "nodes": nodes, "synthetic_router": synthetic}
