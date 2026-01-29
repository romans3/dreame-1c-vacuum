from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

class DreameBatterySensor(SensorEntity):
    """Battery sensor for Dreame vacuum."""

    def __init__(self, vacuum_entity):
        self._vacuum = vacuum_entity
        self._attr_name = f"{vacuum_entity.name} Battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"{vacuum_entity._name}_battery"

    @property
    def native_value(self):
        return self._vacuum.battery_percentage
