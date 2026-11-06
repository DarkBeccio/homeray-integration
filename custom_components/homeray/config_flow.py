"""Config and options flow: one entry, settings in the options."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY,
    CONF_EXCLUDE_LABEL,
    CONF_IGNORE_RECHARGEABLE,
    CONF_SILENT_HOURS,
    CONF_SILENT_SCOPE,
    DEFAULTS,
    DOMAIN,
    SCOPE_ALL,
    SCOPE_BATTERY,
)


class HomerayConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Homeray", data={}, options=dict(DEFAULTS))
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HomerayOptionsFlow()


class HomerayOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        cur = {**DEFAULTS, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_SILENT_HOURS, default=cur[CONF_SILENT_HOURS]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=720, step=1, unit_of_measurement="h", mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_SILENT_SCOPE, default=cur[CONF_SILENT_SCOPE]): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=[SCOPE_BATTERY, SCOPE_ALL], translation_key="silent_scope")
                ),
                vol.Required(CONF_BATTERY, default=cur[CONF_BATTERY]): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Required(CONF_IGNORE_RECHARGEABLE, default=cur[CONF_IGNORE_RECHARGEABLE]): selector.BooleanSelector(),
                vol.Optional(CONF_EXCLUDE_LABEL, default=cur[CONF_EXCLUDE_LABEL]): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
