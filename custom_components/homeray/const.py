"""Constants for the Homeray integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "homeray"

CONF_SILENT_HOURS = "silent_hours"
CONF_SILENT_SCOPE = "silent_scope"
CONF_BATTERY = "battery_threshold"
CONF_EXCLUDE_LABEL = "exclude_label"
CONF_IGNORE_RECHARGEABLE = "ignore_rechargeable"

SCOPE_BATTERY = "battery"
SCOPE_ALL = "all"

DEFAULTS = {
    CONF_SILENT_HOURS: 24,
    CONF_SILENT_SCOPE: SCOPE_BATTERY,
    CONF_BATTERY: 20,
    CONF_EXCLUDE_LABEL: "fuori_monitoraggio",
    CONF_IGNORE_RECHARGEABLE: True,
}

UPDATE_INTERVAL = timedelta(minutes=5)

# Labels that place or hide a device on the network map.
LABEL_TYPES = {
    "homeray_router": "router",
    "homeray_switch": "switch",
    "homeray_ap": "ap",
    "homeray_powerline": "plc",
    "homeray_powerline_wifi": "plcwifi",
    "homeray_server": "server",
    "homeray_alarm": "alarm",
}
LABEL_HIDE = "homeray_hide"

# Lists in sensor attributes are capped so the state machine stays small.
ATTR_LIMIT = 50
