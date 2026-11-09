"""Health checks that the dashboard cannot do on its own.

Everything here reads the registries and the state machine; nothing is sent to devices.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY,
    CONF_EXCLUDE_LABEL,
    CONF_IGNORE_RECHARGEABLE,
    CONF_SILENT_HOURS,
    CONF_SILENT_SCOPE,
    SCOPE_BATTERY,
)

BAD_STATES = ("unavailable", "unknown")
MEASURING = ("sensor", "binary_sensor")
LOW_WORDS = ("low", "critical", "empty", "very_low")
RECHARGEABLE_PLATFORMS = ("mobile_app",)


def _device_name(dev: dr.DeviceEntry) -> str:
    return dev.name_by_user or dev.name or dev.id


def _is_battery(ent: er.RegistryEntry | None, st: State) -> bool:
    dc = st.attributes.get("device_class")
    if dc == "battery":
        return True
    if dc != "enum":
        return False
    hint = " ".join(
        str(x or "")
        for x in (
            st.entity_id,
            ent and ent.translation_key,
            ent and ent.original_name,
            st.attributes.get("friendly_name"),
        )
    ).lower()
    return "batter" in hint


def _excluded(dev: dr.DeviceEntry | None, ent: er.RegistryEntry | None, label: str) -> bool:
    if not label:
        return False
    return bool((dev and label in dev.labels) or (ent and label in ent.labels))


def _devices(hass: HomeAssistant):
    """Enabled, real devices with their enabled entities and current states."""
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    for dev in dev_reg.devices.values():
        if dev.disabled_by or dev.entry_type == dr.DeviceEntryType.SERVICE:
            continue
        rows = []
        for ent in er.async_entries_for_device(ent_reg, dev.id):
            st = hass.states.get(ent.entity_id)
            if st is not None:
                rows.append((ent, st))
        yield dev, rows


def tracking_since(hass: HomeAssistant) -> datetime | None:
    """Oldest last_reported in the state machine: a safe estimate of when tracking began.

    last_reported starts again at every restart, so a device cannot be judged silent
    for longer than this.
    """
    oldest = None
    for st in hass.states.async_all():
        lr = getattr(st, "last_reported", None) or st.last_updated
        if oldest is None or lr < oldest:
            oldest = lr
    return oldest


def silent_devices(hass: HomeAssistant, opts: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Devices that still look available but have not reported anything for a while.

    This is the case the built-in checks miss: a battery device that died at 80 % keeps its
    last values and is never marked unavailable.
    """
    now = now or dt_util.utcnow()
    hours = float(opts[CONF_SILENT_HOURS])
    label = opts[CONF_EXCLUDE_LABEL]
    since = tracking_since(hass)
    tracked_h = (now - since).total_seconds() / 3600 if since else 0.0
    out: list[dict[str, Any]] = []
    if tracked_h >= hours:
        for dev, rows in _devices(hass):
            if label and label in dev.labels:
                continue
            good = [(e, s) for e, s in rows if s.state not in BAD_STATES and not _excluded(None, e, label)]
            if not any(s.domain in MEASURING for _, s in good):
                continue  # nothing to judge, or the whole device is unavailable (that is "not responding")
            if opts[CONF_SILENT_SCOPE] == SCOPE_BATTERY and not any(_is_battery(e, s) for e, s in rows):
                continue
            if opts[CONF_IGNORE_RECHARGEABLE] and any(e.platform in RECHARGEABLE_PLATFORMS for e, _ in rows):
                continue  # a phone app that goes quiet is normal (closed app, phone away)
            last = max(getattr(s, "last_reported", None) or s.last_updated for _, s in good)
            age = (now - last).total_seconds() / 3600
            if age >= hours:
                out.append(
                    {
                        "device_id": dev.id,
                        "name": _device_name(dev),
                        "area_id": dev.area_id,
                        "model": dev.model or dev.manufacturer or "",
                        "last_reported": last.isoformat(),
                        "hours": round(age, 1),
                    }
                )
    out.sort(key=lambda x: -x["hours"])
    return {
        "devices": out,
        "ready": tracked_h >= hours,
        "ready_in_hours": max(0.0, round(hours - tracked_h, 1)),
        "hours": hours,
    }


def _rechargeable(rows) -> bool:
    for ent, st in rows:
        dc = st.attributes.get("device_class")
        if dc in ("battery_charging", "energy_storage"):
            return True
        if ent.platform in RECHARGEABLE_PLATFORMS:
            return True
    return False


def low_batteries(hass: HomeAssistant, opts: dict[str, Any]) -> list[dict[str, Any]]:
    """Low batteries from percentage, binary and low/medium/high sensors, one row per device."""
    lim = float(opts[CONF_BATTERY])
    label = opts[CONF_EXCLUDE_LABEL]
    best: dict[str, dict[str, Any]] = {}
    rank = {"level": 0, "low": 1, "unavailable": 2}

    def add(key: str, item: dict[str, Any]) -> None:
        cur = best.get(key)
        if cur is None or rank[item["kind"]] < rank[cur["kind"]] or (
            item["kind"] == cur["kind"] == "level" and item["level"] < cur["level"]
        ):
            best[key] = item

    for dev, rows in _devices(hass):
        if label and label in dev.labels:
            continue
        if opts[CONF_IGNORE_RECHARGEABLE] and _rechargeable(rows):
            continue
        dev_ok = any(s.state not in BAD_STATES for _, s in rows)
        for ent, st in rows:
            if _excluded(None, ent, label) or not _is_battery(ent, st):
                continue
            base = {
                "entity_id": st.entity_id,
                "device_id": dev.id,
                "name": st.attributes.get("friendly_name") or _device_name(dev),
            }
            if st.state in BAD_STATES:
                # a battery that stopped reporting while the rest of the device still works
                if dev_ok and st.domain == "sensor":
                    add(dev.id, {**base, "kind": "unavailable", "level": None})
                continue
            if st.domain == "binary_sensor":
                if st.state == "on":
                    add(dev.id, {**base, "kind": "low", "level": None})
                continue
            if st.attributes.get("device_class") == "enum":
                if str(st.state).lower() in LOW_WORDS:
                    add(dev.id, {**base, "kind": "low", "level": None, "text": st.state})
                continue
            try:
                lvl = float(st.state)
            except (TypeError, ValueError):
                continue
            if lvl < lim:
                add(dev.id, {**base, "kind": "level", "level": round(lvl)})
    out = list(best.values())
    out.sort(key=lambda x: (rank[x["kind"]], x["level"] if x["level"] is not None else 0))
    return out
