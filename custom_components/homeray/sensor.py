"""Two sensors, handy for notifications and automations."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomerayConfigEntry, HomerayCoordinator
from .const import ATTR_LIMIT, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: HomerayConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    coord = entry.runtime_data
    async_add_entities([SilentSensor(coord), BatterySensor(coord)])


class _Base(CoordinatorEntity[HomerayCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "devices"

    def __init__(self, coord: HomerayCoordinator, key: str) -> None:
        super().__init__(coord)
        self._attr_translation_key = key
        self._attr_unique_id = f"{coord.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coord.config_entry.entry_id)},
            name="Homeray",
            manufacturer="DarkBeccio",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://homeray.app",
        )


class SilentSensor(_Base):
    _attr_icon = "mdi:access-point-off"

    def __init__(self, coord: HomerayCoordinator) -> None:
        super().__init__(coord, "silent_devices")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["silent"]["devices"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = self.coordinator.data["silent"]
        return {
            "devices": [{"name": d["name"], "device_id": d["device_id"], "hours": d["hours"]} for d in s["devices"][:ATTR_LIMIT]],
            "silent_after_hours": s["hours"],
            "ready": s["ready"],
        }


class BatterySensor(_Base):
    _attr_icon = "mdi:battery-alert-variant-outline"

    def __init__(self, coord: HomerayCoordinator) -> None:
        super().__init__(coord, "low_batteries")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["batteries"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "batteries": [
                {"name": b["name"], "entity_id": b["entity_id"], "kind": b["kind"], "level": b["level"]}
                for b in self.coordinator.data["batteries"][:ATTR_LIMIT]
            ]
        }
