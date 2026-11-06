from homeassistant.helpers import area_registry as ar, floor_registry as fr

from custom_components.homeray.network import discover

from .helpers import device, entity, entry


async def _home(hass):
    floors = fr.async_get(hass)
    top = floors.async_create("First floor", level=1)
    ground = floors.async_create("Ground floor", level=0)
    areas = ar.async_get(hass)
    study = areas.async_create("Study", floor_id=top.floor_id)
    hall = areas.async_create("Hall", floor_id=ground.floor_id)
    return study, hall


async def test_discover_full_home(hass):
    study, hall = await _home(hass)
    fritz = entry(hass, "fritz", data={"host": "192.168.1.1"})
    box = device(hass, fritz, "FRITZ!Box 7590", model="FRITZ!Box 7590", mac="aa:aa:aa:aa:aa:01", area_id=hall.id)
    unifi = entry(hass, "unifi")
    device(hass, unifi, "Upstairs AP", model="U6-Lite", mac="aa:aa:aa:aa:aa:02", area_id=study.id)
    sw = device(hass, unifi, "Office switch", model="USW-Lite-8-PoE", mac="aa:aa:aa:aa:aa:03", area_id=study.id)
    devolo = entry(hass, "devolo_home_network")
    plc = device(hass, devolo, "Garage plug", model="Magic 2 WiFi next", via=(unifi.domain, "Office switch"))
    entity(hass, devolo, plc, "switch", "wifi", "on", translation_key="switch_guest_wifi")
    upnp = entry(hass, "upnp")
    device(hass, upnp, "UPnP box", model="FRITZ!Box 7590")  # same box seen by UPnP, dropped
    other = entry(hass, "zha")
    device(hass, other, "Lamp", model="TRADFRI bulb")  # not network gear
    # status: tracker gives the AP address, a Ping entry watches it
    trk = entry(hass, "unifi_trk")
    hass.states.async_set("device_tracker.ap", "home", {"mac": "AA:AA:AA:AA:AA:02", "ip": "192.168.1.20", "source_type": "router"})
    ping = entry(hass, "ping", data={}, options={"host": "192.168.1.20"})
    pe = entity(hass, ping, None, "binary_sensor", "p1", "on", device_class="connectivity")
    del trk

    r = discover(hass)
    assert [f["name"] for f in r["floors"]] == ["First floor", "Ground floor"]
    by = {n["name"]: n for n in r["nodes"]}
    assert set(by) == {"FRITZ!Box 7590", "Upstairs AP", "Office switch", "Garage plug"}
    assert by["FRITZ!Box 7590"]["type"] == "router" and by["FRITZ!Box 7590"]["parent"] is None
    assert by["FRITZ!Box 7590"]["ip"] == "192.168.1.1"
    assert by["Upstairs AP"]["type"] == "ap" and by["Upstairs AP"]["entity"] == pe
    assert by["Upstairs AP"]["ip"] == "192.168.1.20"
    assert by["Office switch"]["type"] == "switch" and by["Office switch"]["floor_id"] == "first_floor"
    assert by["Garage plug"]["type"] == "plcwifi" and by["Garage plug"]["parent"] == by["Office switch"]["id"]
    assert by["Upstairs AP"]["parent"] == by["FRITZ!Box 7590"]["id"]
    assert r["synthetic_router"] is False
    assert box.id == by["FRITZ!Box 7590"]["device_id"]


async def test_labels_and_synthetic_router(hass):
    cfg = entry(hass, "esphome")
    device(hass, cfg, "Rack switch", labels=["homeray_switch"])
    unifi = entry(hass, "unifi")
    device(hass, unifi, "Hidden AP", model="U6-Pro", labels=["homeray_hide"])
    r = discover(hass)
    assert r["synthetic_router"] is True
    assert [n["type"] for n in r["nodes"]] == ["router", "switch"]
    assert r["nodes"][1]["parent"] == "router"
    assert r["floors"] == []


async def test_home_assistant_host_is_always_up(hass):
    hassio = entry(hass, "hassio")
    device(hass, hassio, "Home Assistant Host", model="Home Assistant Host")
    r = discover(hass)
    ha = [n for n in r["nodes"] if n["type"] == "server"][0]
    assert ha["up"] is True


async def test_duplicate_names_get_unique_ids(hass):
    unifi = entry(hass, "unifi")
    device(hass, unifi, "AP", model="U6-Lite", mac="bb:00:00:00:00:01")
    unifi2 = entry(hass, "unifi")
    device(hass, unifi2, "AP", model="U6-Lite", mac="bb:00:00:00:00:02")
    ids = [n["id"] for n in discover(hass)["nodes"]]
    assert len(ids) == len(set(ids))
