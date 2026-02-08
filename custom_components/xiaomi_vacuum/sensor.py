"""Sensors for Xiaomi Vacuum 1C."""

import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DATA_COORDINATOR, DATA_CLIENT

_LOGGER = logging.getLogger(__name__)


ERROR_CODE_TO_ERROR = {
    0: "NoError",
    1: "Drop",
    2: "Cliff",
    3: "Bumper",
    4: "Gesture",
    5: "Bumper_repeat",
    6: "Drop_repeat",
    7: "Optical_flow",
    8: "No_box",
    9: "No_tankbox",
    10: "Waterbox_empty",
    11: "Box_full",
    12: "Brush",
    13: "Side_brush",
    14: "Fan",
    15: "Left_wheel_motor",
    16: "Right_wheel_motor",
    17: "Turn_suffocate",
    18: "Forward_suffocate",
    19: "Charger_get",
    20: "Battery_low",
    21: "Charge_fault",
    22: "Battery_percentage",
    23: "Heart",
    24: "Camera_occlusion",
    25: "Camera_fault",
    26: "Event_battery",
    27: "Forward_looking",
    28: "Gyroscope",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]

    coordinator = data[DATA_COORDINATOR]
    client = data[DATA_CLIENT]

    name = entry.data.get("name")
    uid = f"xiaomi_vacuum_{name.lower().replace(' ', '_')}"

    entities = [
        DreameBatterySensor(name, uid, coordinator),
        DreameErrorSensor(name, uid, coordinator),
        DreameCleaningAreaSensor(name, uid, coordinator),
        DreameCleaningTimeSensor(name, uid, coordinator),
        DreameMainBrushLifeSensor(name, uid, coordinator),
        DreameSideBrushLifeSensor(name, uid, coordinator),
        DreameFilterLifeSensor(name, uid, coordinator),
        DreameMainBrushTimeLeftSensor(name, uid, coordinator),
        DreameSideBrushTimeLeftSensor(name, uid, coordinator),
        DreameFilterTimeLeftSensor(name, uid, coordinator),
        DreameTotalCleaningCountSensor(name, uid, coordinator),
        DreameTotalCleaningAreaSensor(name, uid, coordinator),
        VacuumLastSeenSensor(name, uid, coordinator),
        VacuumStatusSensor(name, uid, coordinator),  # <── NUOVO SENSORE
    ]

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# BASE CLASS
# ---------------------------------------------------------------------------

class DreameBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for all Dreame sensors."""

    def __init__(self, name, uid, coordinator):
        super().__init__(coordinator)

        self._vacuum_name = name
        self._vacuum_uid = uid

        # DeviceInfo minimal → eredita quello avanzato dal vacuum
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uid)}
        )


# ---------------------------------------------------------------------------
# VACUUM STATUS SENSOR (NUOVO)
# ---------------------------------------------------------------------------

class VacuumStatusSensor(DreameBaseSensor):
    """Unified status sensor with friendly text and booleans."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Status"
        self._attr_unique_id = f"{uid}_status"
        self._attr_icon = "mdi:robot-vacuum"

    @property
    def native_value(self):
        """Return the raw status (cleaning, paused, docked, etc.)."""
        state = self.coordinator.data
        if not state:
            return "offline"

        # Mapping come nel vacuum
        status_map = {
            1: "cleaning",
            2: "idle",
            3: "paused",
            4: "error",
            5: "returning",
            6: "docked",
        }

        status = status_map.get(getattr(state, "status", 2), "idle")
        return status

    @property
    def extra_state_attributes(self):
        """Return friendly status and boolean flags."""
        status = self.native_value

        friendly_status = {
            "cleaning": "Pulizia in corso",
            "paused": "In pausa",
            "returning": "Tornando alla base",
            "docked": "In carica",
            "idle": "In attesa",
            "error": "Errore",
        }.get(status, "Sconosciuto")

        return {
            "friendly_status": friendly_status,
            "is_cleaning": status == "cleaning",
            "is_paused": status == "paused",
            "is_returning": status == "returning",
            "is_docked": status == "docked",
            "is_idle": status == "idle",
            "is_error": status == "error",
        }


# ---------------------------------------------------------------------------
# BATTERY SENSOR
# ---------------------------------------------------------------------------

class DreameBatterySensor(DreameBaseSensor):
    """Battery sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Battery"
        self._attr_unique_id = f"{uid}_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        state = self.coordinator.data
        return int(getattr(state, "battery", 0) or 0)


# ---------------------------------------------------------------------------
# ERROR SENSOR
# ---------------------------------------------------------------------------

class DreameErrorSensor(DreameBaseSensor):
    """Error code sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Error"
        self._attr_unique_id = f"{uid}_error"

    @property
    def icon(self):
        state = self.coordinator.data
        if not state:
            return "mdi:cloud-off-outline"
        return "mdi:alert-circle-outline" if getattr(state, "error", 0) != 0 else "mdi:check-circle-outline"

    @property
    def native_value(self):
        state = self.coordinator.data
        if not state:
            return "offline"
        return ERROR_CODE_TO_ERROR.get(getattr(state, "error", None), "Unknown")


# ---------------------------------------------------------------------------
# CLEANING AREA SENSOR
# ---------------------------------------------------------------------------

class DreameCleaningAreaSensor(DreameBaseSensor):
    """Cleaning area sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Cleaning Area"
        self._attr_unique_id = f"{uid}_cleaning_area"
        self._attr_native_unit_of_measurement = "m²"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:ruler-square"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "area", 0) or 0


# ---------------------------------------------------------------------------
# CLEANING TIME SENSOR
# ---------------------------------------------------------------------------

class DreameCleaningTimeSensor(DreameBaseSensor):
    """Cleaning time sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Cleaning Time"
        self._attr_unique_id = f"{uid}_cleaning_time"
        self._attr_native_unit_of_measurement = "min"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:timer-outline"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "timer", 0) or 0


# ---------------------------------------------------------------------------
# MAIN BRUSH LIFE SENSOR
# ---------------------------------------------------------------------------

class DreameMainBrushLifeSensor(DreameBaseSensor):
    """Main brush life sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Main Brush Life"
        self._attr_unique_id = f"{uid}_main_brush_life"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:car-turbocharger"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "brush_life_level", 0) or 0


# ---------------------------------------------------------------------------
# SIDE BRUSH LIFE SENSOR
# ---------------------------------------------------------------------------

class DreameSideBrushLifeSensor(DreameBaseSensor):
    """Side brush life sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Side Brush Life"
        self._attr_unique_id = f"{uid}_side_brush_life"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:pinwheel-outline"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "brush_life_level2", 0) or 0


# ---------------------------------------------------------------------------
# FILTER LIFE SENSOR
# ---------------------------------------------------------------------------

class DreameFilterLifeSensor(DreameBaseSensor):
    """Filter life sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Filter Life"
        self._attr_unique_id = f"{uid}_filter_life"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:air-filter"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "filter_life_level", 0) or 0


# ---------------------------------------------------------------------------
# MAIN BRUSH TIME LEFT SENSOR
# ---------------------------------------------------------------------------

class DreameMainBrushTimeLeftSensor(DreameBaseSensor):
    """Main brush time left sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Main Brush Time Left"
        self._attr_unique_id = f"{uid}_main_brush_time_left"
        self._attr_native_unit_of_measurement = "h"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:car-turbocharger"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "brush_left_time", 0) or 0


# ---------------------------------------------------------------------------
# SIDE BRUSH TIME LEFT SENSOR
# ---------------------------------------------------------------------------

class DreameSideBrushTimeLeftSensor(DreameBaseSensor):
    """Side brush time left sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Side Brush Time Left"
        self._attr_unique_id = f"{uid}_side_brush_time_left"
        self._attr_native_unit_of_measurement = "h"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:pinwheel-outline"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "brush_left_time2", 0) or 0


# ---------------------------------------------------------------------------
# FILTER TIME LEFT SENSOR
# ---------------------------------------------------------------------------

class DreameFilterTimeLeftSensor(DreameBaseSensor):
    """Filter time left sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Filter Time Left"
        self._attr_unique_id = f"{uid}_filter_left_time"
        self._attr_native_unit_of_measurement = "h"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:air-filter"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "filter_left_time", 0) or 0


# ---------------------------------------------------------------------------
# TOTAL CLEANING COUNT SENSOR
# ---------------------------------------------------------------------------

class DreameTotalCleaningCountSensor(DreameBaseSensor):
    """Total cleaning count sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Total Cleaning Count"
        self._attr_unique_id = f"{uid}_total_cleaning_count"
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "total_clean_count", 0) or 0


# ---------------------------------------------------------------------------
# TOTAL CLEANING AREA SENSOR
# ---------------------------------------------------------------------------

class DreameTotalCleaningAreaSensor(DreameBaseSensor):
    """Total cleaning area sensor."""

    def __init__(self, name, uid, coordinator):
        super().__init__(name, uid, coordinator)

        self._attr_name = f"{name} Total Cleaning Area"
        self._attr_unique_id = f"{uid}_total_cleaning_area"
        self._attr_native_unit_of_measurement = "m²"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:set-square"

    @property
    def native_value(self):
        state = self.coordinator.data
        return getattr(state, "total_area", 0) or 0


# ---------------------------------------------------------------------------
# VACUUM LAST SEEN SENSOR
# ---------------------------------------------------------------------------

class VacuumLastSeenSensor(CoordinatorEntity, SensorEntity):
    """Sensor reporting last successful communication."""

    _attr_icon = "mdi:clock-outline"

    def __init__(self, name, uid, coordinator):
        super().__init__(coordinator)
        self._attr_name = f"{name} Last Seen"
        self._attr_unique_id = f"{uid}_last_seen"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uid)}
        )

        self._last_seen = None

    @property
    def native_value(self):
        """Return human-friendly time difference as main state."""
        from homeassistant.util.dt import now, as_local

        if self.coordinator.last_update_success:
            self._last_seen = now()

        if not self._last_seen:
            return "Mai"

        now_local = as_local(now())
        last_local = as_local(self._last_seen)
        diff = (now_local - last_local).total_seconds()

        if diff < 60:
            return f"{int(diff)} secondi fa"
        elif diff < 3600:
            return f"{int(diff // 60)} minuti fa"
        elif diff < 86400:
            return f"{int(diff // 3600)} ore fa"
        else:
            return last_local.strftime("%d %B %Y alle %H:%M")

    @property
    def extra_state_attributes(self):
        """Return raw timestamp and seconds difference."""
        if not self._last_seen:
            return {
                "timestamp": None,
                "seconds_since": None
            }

        from homeassistant.util.dt import now, as_local
        now_local = as_local(now())
        last_local = as_local(self._last_seen)

        diff = (now_local - last_local).total_seconds()

        return {
            "timestamp": self._last_seen.isoformat(),
            "seconds_since": int(diff)
        }