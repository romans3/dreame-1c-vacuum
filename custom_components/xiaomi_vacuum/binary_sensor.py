"""Diagnostic binary sensors for Xiaomi Vacuum 1C."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DATA_COORDINATOR


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up diagnostic binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]

    name = entry.data.get("name")
    uid = f"xiaomi_vacuum_{name.lower().replace(' ', '_')}"

    async_add_entities([VacuumOnlineBinarySensor(name, uid, coordinator)])


class VacuumOnlineBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating if the vacuum is online."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, name, uid, coordinator):
        super().__init__(coordinator)
        self._attr_name = f"{name} Online"
        self._attr_unique_id = f"{uid}_online"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uid)},
            name=name,
            manufacturer="Dreame",
            model="Vacuum 1C",
        )

    @property
    def is_on(self):
        """Return True if the vacuum is reachable."""
        return self.coordinator.last_update_success