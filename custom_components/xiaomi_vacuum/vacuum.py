"""Xiaomi Vacuum 1C – HA 2026+ compatible"""
from functools import partial
import logging
import voluptuous as vol

from homeassistant.components.vacuum import (
    PLATFORM_SCHEMA,
    StateVacuumEntity,
    VacuumEntityFeature,
    VacuumActivity,
)

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.helpers import config_validation as cv

from .miio import DreameVacuum, DeviceException

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi vacuum cleaner"
DATA_KEY = "vacuum.xiaomi_vacuum"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

ATTR_STATUS = "status"
ATTR_ERROR = "error"
ATTR_FAN_SPEED = "fan_speed"
ATTR_CLEANING_TIME = "cleaning_time"
ATTR_CLEANING_AREA = "cleaning_area"
ATTR_MAIN_BRUSH_LEFT_TIME = "main_brush_time_left"
ATTR_MAIN_BRUSH_LIFE_LEVEL = "main_brush_life_level"
ATTR_SIDE_BRUSH_LEFT_TIME = "side_brush_time_left"
ATTR_SIDE_BRUSH_LIFE_LEVEL = "side_brush_life_level"
ATTR_FILTER_LIFE_LEVEL = "filter_life_level"
ATTR_FILTER_LEFT_TIME = "filter_left_time"
ATTR_CLEANING_TOTAL_TIME = "total_cleaning_count"
ATTR_CLEANING_TOTAL_AREA = "total_cleaning_area"
ATTR_WATER_LEVEL = "water_level"
ATTR_WATER_LEVEL_LIST = "water_level_list"

SUPPORT_XIAOMI = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.SEND_COMMAND
)

SPEED_CODE_TO_NAME = {
    0: "Silent",
    1: "Standard",
    2: "Strong",
    3: "Turbo",
}

WATER_CODE_TO_NAME = {
    1: "Low",
    2: "Medium",
    3: "High",
}

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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Xiaomi vacuum cleaner platform."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config.get(CONF_HOST)
    token = config.get(CONF_TOKEN)
    name = config.get(CONF_NAME)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token)
    vacuum = DreameVacuum(host, token)

    vacuum_entity = DreameVacuumEntity(name, vacuum)
    battery_entity = DreameBatterySensor(vacuum_entity)

    hass.data[DATA_KEY][host] = vacuum_entity

    async_add_entities([vacuum_entity, battery_entity], update_before_add=True)


class DreameVacuumEntity(StateVacuumEntity):
    """Representation of a Xiaomi vacuum cleaner robot."""

    def __init__(self, name, vacuum):
        self._name = name
        self._vacuum = vacuum

        # Unique ID per Home Assistant
        self._attr_unique_id = f"xiaomi_vacuum_{name.lower().replace(' ', '_')}"

        self._fan_speeds = None
        self._fan_speeds_reverse = None
        self._current_fan_speed = None

        self.vacuum_state = None
        self.vacuum_error = None
        self.battery_percentage = None

        self._main_brush_time_left = None
        self._main_brush_life_level = None

        self._side_brush_time_left = None
        self._side_brush_life_level = None

        self._filter_life_level = None
        self._filter_left_time = None

        self._total_clean_count = None
        self._total_area = None

        self._cleaning_area = None
        self._cleaning_time = None

        self._water_level = None
        self._current_water_level = None
        self._water_level_reverse = None

    #
    # NEW API — activity replaces state
    #
    @property
    def activity(self):
        """Return the activity of the vacuum using the new HA API."""
        if self.vacuum_state is None:
            return None

        mapping = {
            1: VacuumActivity.CLEANING,
            2: VacuumActivity.IDLE,
            3: VacuumActivity.PAUSED,
            4: VacuumActivity.ERROR,
            5: VacuumActivity.RETURNING,
            6: VacuumActivity.DOCKED,
        }

        return mapping.get(int(self.vacuum_state), VacuumActivity.IDLE)

    #
    # Deprecated state property — kept only for backward compatibility
    #
    @property
    def state(self):
        return self.activity

    @property
    def name(self):
        return self._name

    @property
    def error(self):
        if self.vacuum_error is not None:
            return ERROR_CODE_TO_ERROR.get(self.vacuum_error, "Unknown")

    @property
    def fan_speed(self):
        if self.vacuum_state is not None:
            speed = self._current_fan_speed
            if speed in self._fan_speeds_reverse:
                return SPEED_CODE_TO_NAME.get(self._current_fan_speed, "Unknown")
            return speed

    @property
    def fan_speed_list(self):
        return list(self._fan_speeds_reverse)

    @property
    def water_level(self):
        if self.vacuum_state is not None:
            water = self._current_water_level
            if water in self._water_level_reverse:
                return WATER_CODE_TO_NAME.get(self._current_water_level, "Unknown")
            return water

    @property
    def water_level_list(self):
        return list(self._water_level_reverse)

    @property
    def extra_state_attributes(self):
        if self.vacuum_state is not None:
            return {
                ATTR_STATUS: str(self.activity),
                ATTR_ERROR: ERROR_CODE_TO_ERROR.get(self.vacuum_error, "Unknown"),
                ATTR_FAN_SPEED: SPEED_CODE_TO_NAME.get(self._current_fan_speed, "Unknown"),
                ATTR_MAIN_BRUSH_LEFT_TIME: self._main_brush_time_left,
                ATTR_MAIN_BRUSH_LIFE_LEVEL: self._main_brush_life_level,
                ATTR_SIDE_BRUSH_LEFT_TIME: self._side_brush_time_left,
                ATTR_SIDE_BRUSH_LIFE_LEVEL: self._side_brush_life_level,
                ATTR_FILTER_LIFE_LEVEL: self._filter_life_level,
                ATTR_FILTER_LEFT_TIME: self._filter_left_time,
                ATTR_CLEANING_AREA: self._cleaning_area,
                ATTR_CLEANING_TOTAL_AREA: self._total_area,
                ATTR_CLEANING_TIME: self._cleaning_time,
                ATTR_CLEANING_TOTAL_TIME: self._total_clean_count,
                ATTR_WATER_LEVEL: WATER_CODE_TO_NAME.get(self._current_water_level, "Unknown"),
                ATTR_WATER_LEVEL_LIST: ["Low", "Medium", "High"],
            }

    @property
    def supported_features(self):
        return SUPPORT_XIAOMI

    async def _try_command(self, mask_error, func, *args, **kwargs):
        try:
            await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
            return True
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            return False

    async def async_locate(self, **kwargs):
        await self._try_command("Unable to locate the botvac: %s", self._vacuum.find)

    async def async_start(self):
        await self._try_command("Unable to start the vacuum: %s", self._vacuum.start)

    async def async_stop(self, **kwargs):
        await self._try_command("Unable to stop the vacuum: %s", self._vacuum.stop)

    async def async_pause(self):
        await self._try_command("Unable to pause the vacuum: %s", self._vacuum.stop)

    async def async_return_to_base(self, **kwargs):
        await self._try_command("Unable to return home: %s", self._vacuum.return_home)

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        if fan_speed in self._fan_speeds_reverse:
            fan_speed = self._fan_speeds_reverse[fan_speed]
        else:
            try:
                fan_speed = int(fan_speed)
            except ValueError:
                _LOGGER.error("Invalid fan speed. Valid: %s", self.fan_speed_list)
                return
        await self._try_command("Unable to set fan speed: %s", self._vacuum.set_fan_speed, fan_speed)

    async def set_water_level(self, water_level, **kwargs):
        if water_level in self._water_level_reverse:
            water_level = self._water_level_reverse[water_level]
        else:
            try:
                water_level = int(water_level)
            except ValueError:
                _LOGGER.error("Invalid water level. Valid: %s", self.water_level_list)
                return
        await self._try_command("Unable to set water level: %s", self._vacuum.set_water_level, water_level)

    async def async_send_command(self, command, params, **kwargs):
        if command == "set_water_level":
            await self.set_water_level(params["water_level"])
        else:
            raise NotImplementedError()

    def update(self):
        try:
            state = self._vacuum.status()

            self.vacuum_state = state.status
            self.vacuum_error = state.error

            self._fan_speeds = SPEED_CODE_TO_NAME
            self._fan_speeds_reverse = {v: k for k, v in self._fan_speeds.items()}
            self._current_fan_speed = state.fan_speed

            self.battery_percentage = state.battery

            self._total_clean_count = state.total_clean_count
            self._total_area = state.total_area

            self._main_brush_time_left = state.brush_left_time
            self._main_brush_life_level = state.brush_life_level

            self._side_brush_time_left = state.brush_left_time2
            self._side_brush_life_level = state.brush_life_level2

            self._filter_life_level = state.filter_life_level
            self._filter_left_time = state.filter_left_time

            self._cleaning_area = state.area
            self._cleaning_time = state.timer

            self._water_level = WATER_CODE_TO_NAME
            self._water_level_reverse = {v: k for k, v in self._water_level.items()}
            self._current_water_level = state.water_level

        except OSError as exc:
            _LOGGER.error("Got OSError while fetching the state: %s", exc)


#
# NEW: Battery sensor (required by HA 2026+)
#
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
