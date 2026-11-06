from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry


def entry(hass, domain, data=None, options=None):
    e = MockConfigEntry(domain=domain, data=data or {}, options=options or {})
    e.add_to_hass(hass)
    return e


def device(hass, cfg, name, model=None, mac=None, area_id=None, via=None, labels=None, manufacturer=None):
    reg = dr.async_get(hass)
    d = reg.async_get_or_create(
        config_entry_id=cfg.entry_id,
        identifiers={(cfg.domain, name)},
        connections={(dr.CONNECTION_NETWORK_MAC, mac)} if mac else set(),
        name=name, model=model, manufacturer=manufacturer,
        via_device=via,
    )
    upd = {}
    if area_id:
        upd["area_id"] = area_id
    if labels:
        upd["labels"] = set(labels)
    if upd:
        d = reg.async_update_device(d.id, **upd)
    return d


def entity(hass, cfg, dev, domain, uid, state, attrs=None, device_class=None, translation_key=None, labels=None):
    reg = er.async_get(hass)
    e = reg.async_get_or_create(domain, cfg.domain, uid, config_entry=cfg, device_id=dev.id if dev else None,
                                original_device_class=device_class, translation_key=translation_key)
    if labels:
        e = reg.async_update_entity(e.entity_id, labels=set(labels))
    a = dict(attrs or {})
    if device_class:
        a.setdefault("device_class", device_class)
    hass.states.async_set(e.entity_id, state, a)
    return e.entity_id
