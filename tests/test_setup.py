from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.homeray.const import DOMAIN

from .helpers import device, entity, entry


async def _setup(hass):
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] is FlowResultType.FORM
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return r["result"]


async def test_flow_single_instance_and_options(hass):
    e = await _setup(hass)
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert r["type"] is FlowResultType.ABORT
    r = await hass.config_entries.options.async_init(e.entry_id)
    r = await hass.config_entries.options.async_configure(
        r["flow_id"],
        {"silent_hours": 12, "silent_scope": "all", "battery_threshold": 30, "ignore_rechargeable": False, "exclude_label": "x"},
    )
    assert r["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert e.options["silent_hours"] == 12


async def test_sensors_and_websocket(hass, hass_ws_client):
    cfg = entry(hass, "zha")
    d = device(hass, cfg, "Remote")
    entity(hass, cfg, d, "sensor", "p", "5", device_class="battery")
    await _setup(hass)
    st = hass.states.get("sensor.homeray_low_batteries")
    assert st is not None and st.state == "1"
    assert st.attributes["batteries"][0]["level"] == 5
    assert hass.states.get("sensor.homeray_silent_devices").state == "0"

    ws = await hass_ws_client(hass)
    await ws.send_json({"id": 1, "type": "homeray/status"})
    msg = await ws.receive_json()
    assert msg["success"] and msg["result"]["batteries"][0]["kind"] == "level"
    assert msg["result"]["silent"]["ready"] is False
    await ws.send_json({"id": 2, "type": "homeray/network"})
    msg = await ws.receive_json()
    assert msg["success"] and msg["result"]["nodes"][0]["type"] == "router"


async def test_unload(hass):
    e = await _setup(hass)
    assert await hass.config_entries.async_unload(e.entry_id)


async def test_websocket_requires_admin(hass, hass_ws_client, hass_read_only_access_token):
    await _setup(hass)
    ws = await hass_ws_client(hass, hass_read_only_access_token)
    for i, cmd in enumerate(("homeray/status", "homeray/network"), start=1):
        await ws.send_json({"id": i, "type": cmd})
        msg = await ws.receive_json()
        assert not msg["success"]
        assert msg["error"]["code"] == "unauthorized"
