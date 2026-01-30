"""DataUpdateCoordinator for Xiaomi Vacuum 1C."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_NAME, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_create_coordinator(hass: HomeAssistant, client, entry) -> DataUpdateCoordinator:
    """Create and initialize the DataUpdateCoordinator for the Xiaomi Vacuum 1C."""

    # Leggi polling_interval dalle options (default a DEFAULT_UPDATE_INTERVAL)
    polling_interval = entry.options.get("polling_interval", DEFAULT_UPDATE_INTERVAL)

    async def async_update_data():
        """Fetch data from the device."""
        try:
            # DreameVacuum.status() is blocking → run in executor
            state = await hass.async_add_executor_job(client.status)
            return state
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Error communicating with Xiaomi Vacuum 1C: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=polling_interval),  # Usa il valore dalle options
    )

    await coordinator.async_config_entry_first_refresh()
    return coordinator