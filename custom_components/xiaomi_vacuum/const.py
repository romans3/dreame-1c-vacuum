"""Constants for Xiaomi Vacuum 1C integration."""

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN

DOMAIN = "xiaomi_vacuum"

DEFAULT_NAME = "Xiaomi Vacuum 1C"

# Config keys
CONF_HOST = CONF_HOST
CONF_TOKEN = CONF_TOKEN
CONF_NAME = CONF_NAME

# Data keys in hass.data
DATA_COORDINATOR = "coordinator"
DATA_CLIENT = "client"

# Platforms
PLATFORMS: list[str] = ["vacuum", "sensor", "binary_sensor"]

# Update interval (seconds)
DEFAULT_UPDATE_INTERVAL = 15