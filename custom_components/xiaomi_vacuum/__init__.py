"""Xiaomi Vacuum 1C component"""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "xiaomi_vacuum"

async def async_setup(hass: HomeAssistant, config):
    """Set up the Xiaomi Vacuum 1C integration (YAML only)."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Config entries are not used for this integration."""
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True
