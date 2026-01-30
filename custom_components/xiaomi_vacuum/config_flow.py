"""Config flow for Xiaomi Vacuum 1C."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN

from .const import DOMAIN, DEFAULT_NAME


# -----------------------------
# CONFIG FLOW PRINCIPALE
# -----------------------------
class XiaomiVacuumConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi Vacuum 1C."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return XiaomiVacuumOptionsFlow()


# -----------------------------
# OPTIONS FLOW
# -----------------------------

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("polling_interval", default=30): vol.All(int, vol.Range(min=5, max=300)),
        vol.Optional("display_name", default=DEFAULT_NAME): str,
        vol.Optional("default_fan_speed", default="Standard"): vol.In(
            ["Silent", "Standard", "Strong", "Turbo"]
        ),
        vol.Optional("enable_sensors", default=True): bool,
        vol.Optional("debug_mode", default=False): bool,
    }
)


class XiaomiVacuumOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Xiaomi Vacuum 1C."""

    def __init__(self) -> None:
        """Initialize options flow."""
        # eventuale stato interno tuo
        pass

    async def async_step_init(self, user_input=None):
        """Main options menu."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )