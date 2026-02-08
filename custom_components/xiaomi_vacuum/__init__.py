"""Xiaomi Vacuum 1C – modern integration with config_flow."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PLATFORMS,
    DATA_CLIENT,
    DATA_COORDINATOR,
)
from .miio import DreameVacuum
from .coordinator import async_create_coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """YAML setup is no longer used."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    host = entry.data.get("host")
    token = entry.data.get("token")
    name = entry.data.get("name")

    _LOGGER.info("Setting up Xiaomi Vacuum 1C at %s (name: %s)", host, name)

    client = DreameVacuum(host, token)

    # Recupero info reali dal robot (miIO.info)
    try:
        info = client.info()
    except Exception as e:
        _LOGGER.warning("Unable to read device info: %s", e)
        info = None

    coordinator = await async_create_coordinator(hass, client, entry)

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        "device_info_raw": info,   # <── SALVATO QUI
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when entry is updated."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of config entries."""
    # Placeholder for future migrations (versions, data shape, etc.)
    _LOGGER.debug("Migrating Xiaomi Vacuum 1C entry %s, version %s", entry.entry_id, entry.version)
    return True