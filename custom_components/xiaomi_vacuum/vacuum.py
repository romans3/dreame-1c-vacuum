"""Vacuum entity for Xiaomi Vacuum 1C."""

import logging

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
    VacuumActivity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DATA_COORDINATOR, DATA_CLIENT

_LOGGER = logging.getLogger(__name__)


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


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up vacuum entity from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]

    coordinator = data[DATA_COORDINATOR]
    client = data[DATA_CLIENT]

    name = entry.data.get("name")
    info = data.get("device_info_raw")

    vacuum_entity = DreameVacuumEntity(name, coordinator, client, info)
    async_add_entities([vacuum_entity])


class DreameVacuumEntity(StateVacuumEntity, CoordinatorEntity):
    """Representation of the Dreame 1C vacuum."""

    def __init__(self, name, coordinator, client, info):
        StateVacuumEntity.__init__(self)
        CoordinatorEntity.__init__(self, coordinator)

        self._client = client

        # Unique ID stabile e corretto
        uid = f"xiaomi_vacuum_{name.lower().replace(' ', '_')}"
        self._attr_unique_id = uid
        self._attr_name = name
        self._attr_supported_features = SUPPORT_XIAOMI

        # DeviceInfo corretto e compatibile
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uid)},
            name=name,
            manufacturer="Dreame",
            model=getattr(info, "model", "Vacuum 1C") if info else "Vacuum 1C",
            sw_version=getattr(info, "firmware_version", None) if info else None,
            hw_version=getattr(info, "hardware_version", None) if info else None,
            connections={
                ("mac", getattr(info, "mac_address"))
            } if info and getattr(info, "mac_address", None) else None,
            configuration_url=f"http://{getattr(client, 'ip', None)}" if getattr(client, 'ip', None) else None,
        )

    @property
    def activity(self) -> VacuumActivity:
        state = self.coordinator.data
        if not state:
            return VacuumActivity.IDLE

        status = getattr(state, "status", 2)
        try:
            status = int(status)
        except (ValueError, TypeError):
            return VacuumActivity.IDLE

        mapping = {
            1: VacuumActivity.CLEANING,
            2: VacuumActivity.IDLE,
            3: VacuumActivity.PAUSED,
            4: VacuumActivity.ERROR,
            5: VacuumActivity.RETURNING,
            6: VacuumActivity.DOCKED,
        }
        return mapping.get(status, VacuumActivity.IDLE)

    @property
    def fan_speed(self):
        state = self.coordinator.data
        if not state:
            return None
        return SPEED_CODE_TO_NAME.get(getattr(state, "fan_speed", None), "Unknown")

    @property
    def fan_speed_list(self):
        return list(SPEED_CODE_TO_NAME.values())

    @property
    def water_level(self):
        state = self.coordinator.data
        if not state:
            return None
        return WATER_CODE_TO_NAME.get(getattr(state, "water_level", None), "Unknown")

    @property
    def water_level_list(self):
        return list(WATER_CODE_TO_NAME.values())

    @property
    def extra_state_attributes(self):
        state = self.coordinator.data
        if not state:
            return {}

        status = self.activity.name.lower()
        friendly_status = {
            "cleaning": "Pulizia in corso",
            "paused": "In pausa",
            "returning": "Tornando alla base",
            "docked": "In carica",
            "idle": "In attesa",
            "error": "Errore",
        }.get(status, "Sconosciuto")

        return {
            "status": status,
            "friendly_status": friendly_status,
            "is_cleaning": status == "cleaning",
            "is_paused": status == "paused",
            "is_returning": status == "returning",
            "is_docked": status == "docked",
            "is_idle": status == "idle",
            "is_error": status == "error",
            "error": ERROR_CODE_TO_ERROR.get(getattr(state, "error", 0), "Unknown"),
            "cleaning_area": getattr(state, "area", None),
            "cleaning_time": getattr(state, "timer", None),
            "total_cleaning_count": getattr(state, "total_clean_count", None),
            "total_cleaning_area": getattr(state, "total_area", None),
            "main_brush_life_level": getattr(state, "brush_life_level", None),
            "side_brush_life_level": getattr(state, "brush_life_level2", None),
            "filter_life_level": getattr(state, "filter_life_level", None),
            "water_level": WATER_CODE_TO_NAME.get(getattr(state, "water_level", None), "Unknown"),
            "ip_address": getattr(self._client, "ip", None),
        }

    async def _exec(self, label, func, *args):
        try:
            await self.hass.async_add_executor_job(func, *args)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("%s: %s", label, err)

    async def async_start(self):
        await self._exec("Unable to start vacuum", self._client.start)

    async def async_stop(self, **kwargs):
        await self._exec("Unable to stop vacuum", self._client.stop)

    async def async_pause(self):
        state = self.coordinator.data
        if not state:
            return

        status = getattr(state, "status", 2)

        if status == 1:
            await self._exec("Unable to pause vacuum", self._client.stop)
        elif status == 3:
            await self._exec("Unable to resume vacuum", self._client.start)

    async def async_return_to_base(self, **kwargs):
        await self._exec("Unable to return home", self._client.return_home)

    async def async_locate(self, **kwargs):
        await self._exec("Unable to locate vacuum", self._client.find)

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        reverse = {v: k for k, v in SPEED_CODE_TO_NAME.items()}
        if fan_speed not in reverse:
            return
        await self._exec("Unable to set fan speed", self._client.set_fan_speed, reverse[fan_speed])

    async def async_send_command(self, command, params=None, **kwargs):
        if command == "set_water_level":
            reverse = {v: k for k, v in WATER_CODE_TO_NAME.items()}
            level = params.get("water_level")
            if level not in reverse:
                return
            await self._exec(
                "Unable to set water level",
                self._client.set_water_level,
                reverse[level]
            )