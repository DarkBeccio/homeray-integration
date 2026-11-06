from datetime import timedelta

from custom_components.homeray.analysis import low_batteries, silent_devices
from custom_components.homeray.const import DEFAULTS

from .helpers import device, entity, entry

OPTS = dict(DEFAULTS)


async def test_silent_needs_enough_history(hass, freezer):
    cfg = entry(hass, "zha")
    d = device(hass, cfg, "Door")
    entity(hass, cfg, d, "sensor", "bat", "80", {"unit_of_measurement": "%"}, device_class="battery")
    freezer.tick(timedelta(hours=3))
    r = silent_devices(hass, OPTS)
    assert r["ready"] is False and r["devices"] == []
    assert r["ready_in_hours"] == 21


async def test_silent_battery_device(hass, freezer):
    cfg = entry(hass, "zha")
    dead = device(hass, cfg, "Dead door")
    entity(hass, cfg, dead, "sensor", "bat1", "80", device_class="battery")
    entity(hass, cfg, dead, "binary_sensor", "door1", "off", device_class="door")
    alive = device(hass, cfg, "Living sensor")
    a = entity(hass, cfg, alive, "sensor", "bat2", "90", device_class="battery")
    plug = device(hass, cfg, "Plug")  # mains powered: ignored with the default scope
    entity(hass, cfg, plug, "sensor", "pw", "5", device_class="power")
    freezer.tick(timedelta(hours=25))
    hass.states.async_set(a, "90", {"device_class": "battery"}, force_update=True)
    r = silent_devices(hass, OPTS)
    assert r["ready"] is True
    assert [x["name"] for x in r["devices"]] == ["Dead door"]
    assert r["devices"][0]["hours"] == 25

    r_all = silent_devices(hass, {**OPTS, "silent_scope": "all"})
    assert {x["name"] for x in r_all["devices"]} == {"Dead door", "Plug"}


async def test_silent_skips_unavailable_and_excluded(hass, freezer):
    cfg = entry(hass, "zha")
    gone = device(hass, cfg, "Gone")
    entity(hass, cfg, gone, "sensor", "b1", "unavailable", device_class="battery")
    ign = device(hass, cfg, "Ignored", labels=["fuori_monitoraggio"])
    entity(hass, cfg, ign, "sensor", "b2", "50", device_class="battery")
    freezer.tick(timedelta(hours=30))
    assert silent_devices(hass, OPTS)["devices"] == []


async def test_batteries_all_kinds(hass):
    cfg = entry(hass, "zha")
    d1 = device(hass, cfg, "Remote")
    entity(hass, cfg, d1, "sensor", "p", "12", device_class="battery")
    d2 = device(hass, cfg, "Smoke")
    entity(hass, cfg, d2, "binary_sensor", "bl", "on", device_class="battery")
    d3 = device(hass, cfg, "Scale")
    entity(hass, cfg, d3, "sensor", "en", "low", {"options": ["low", "medium", "high"]}, device_class="enum", translation_key="battery")
    d4 = device(hass, cfg, "Thermo")
    entity(hass, cfg, d4, "sensor", "t", "21", device_class="temperature")
    entity(hass, cfg, d4, "sensor", "tb", "unavailable", device_class="battery")
    d5 = device(hass, cfg, "Fine")
    entity(hass, cfg, d5, "sensor", "f", "95", device_class="battery")
    rows = low_batteries(hass, OPTS)
    got = {r["name"]: r["kind"] for r in rows}
    assert got == {"Remote": "level", "Smoke": "low", "Scale": "low", "Thermo": "unavailable"}
    assert rows[0]["kind"] == "level" and rows[0]["level"] == 12


async def test_batteries_one_row_per_device_and_rechargeable(hass):
    cfg = entry(hass, "zha")
    d = device(hass, cfg, "Lock")
    entity(hass, cfg, d, "sensor", "a", "15", device_class="battery")
    entity(hass, cfg, d, "binary_sensor", "b", "on", device_class="battery")
    home = device(hass, cfg, "Storage")
    entity(hass, cfg, home, "sensor", "soc", "8", device_class="battery")
    entity(hass, cfg, home, "sensor", "st", "3.2", device_class="energy_storage")
    rows = low_batteries(hass, OPTS)
    assert len(rows) == 1 and rows[0]["level"] == 15
    assert len(low_batteries(hass, {**OPTS, "ignore_rechargeable": False})) == 2


async def test_battery_threshold_and_entity_label(hass):
    cfg = entry(hass, "zha")
    d = device(hass, cfg, "Sensor")
    entity(hass, cfg, d, "sensor", "x", "30", device_class="battery")
    assert low_batteries(hass, OPTS) == []
    assert len(low_batteries(hass, {**OPTS, "battery_threshold": 40})) == 1
    d2 = device(hass, cfg, "Other")
    entity(hass, cfg, d2, "sensor", "y", "5", device_class="battery", labels=["fuori_monitoraggio"])
    assert len(low_batteries(hass, {**OPTS, "battery_threshold": 40})) == 1
